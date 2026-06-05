"""PDF 生成服务 — HTML → PDF (Playwright Chromium)。

Playwright 浏览器进程级单例 + 专用线程保证 greenlet 亲和性。
临时文件由调用方负责清理。

用法:
    from src_v2.services.pdf_service import generate_pdf, shutdown
    pdf_path = generate_pdf(html_string)
    # ... 使用 pdf_path ...
    # 应用关闭时:
    shutdown()
"""
from __future__ import annotations

import logging
import os
import tempfile
import concurrent.futures
import threading
from pathlib import Path

from pdf_chrome_templates import build_pdf_chrome_options
from pdf_progress_rail import apply_progress_rail
from pdf_utils import (
    _PREFLIGHT_JS,
    _extract_toc_pages,
    _toc_pages_for_injection,
    _TOC_INJECT_JS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Playwright 可用性检测
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright, Browser
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# ---------------------------------------------------------------------------
# 浏览器单例 + 并发控制
# ---------------------------------------------------------------------------

_browser: Browser | None = None
_browser_lock = threading.Lock()

# 专用单线程: 保证 Playwright 所有操作在同一 greenlet (修复 WO-049)
_pdf_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="playwright"
)

# Playwright context manager (需要保持 alive)
_pw_context = None


def _get_browser() -> Browser:
    """获取 Playwright Chromium 浏览器单例 (lazy init, 双重检查锁)。"""
    global _browser, _pw_context

    if _browser is not None and _browser.is_connected():
        return _browser

    with _browser_lock:
        if _browser is not None and _browser.is_connected():
            return _browser

        if not HAS_PLAYWRIGHT:
            raise RuntimeError(
                "playwright 未安装。请运行: pip install playwright && playwright install chromium"
            )

        logger.info("启动 Playwright Chromium 浏览器...")
        _pw_context = sync_playwright().start()
        _browser = _pw_context.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        logger.info("Chromium 浏览器已启动")
        return _browser



# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def generate_pdf(html: str, *, header_meta: dict | None = None) -> Path:
    """线程安全的 PDF 生成入口 (WO-049 修复)。

    将实际工作提交到专用线程, 确保 Playwright 的 greenlet 亲和性。
    如果已在 playwright 线程中, 直接执行。

    future.result() 不设 timeout — 排队等多久都行。
    真正的超时在 _generate_pdf_impl 内部 (page.set_default_timeout)。
    """
    current = threading.current_thread()
    if current.name.startswith("playwright"):
        return _generate_pdf_impl(html, header_meta=header_meta)
    future = _pdf_executor.submit(_generate_pdf_impl, html, header_meta=header_meta)
    return future.result()


def _create_temp_pdf_path() -> Path:
    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False, prefix="report_",
    )
    tmp.close()
    return Path(tmp.name)


def _build_service_pdf_kwargs(
    pdf_path: Path,
    header_meta: dict | None,
) -> dict:
    pdf_kwargs: dict = {
        "path": str(pdf_path),
        "format": "A4",
        "print_background": True,
    }
    if header_meta:
        pdf_kwargs.update(build_pdf_chrome_options(header_meta))
    return pdf_kwargs


def _write_pdf_with_toc(page, pdf_path: Path, pdf_kwargs: dict) -> None:
    pass1_kwargs = {k: v for k, v in pdf_kwargs.items() if k != "path"}
    pdf_bytes = page.pdf(**pass1_kwargs)
    toc_pages = _extract_toc_pages(pdf_bytes)

    if not toc_pages:
        pdf_path.write_bytes(pdf_bytes)
        return

    display_pages = _toc_pages_for_injection(toc_pages)
    injected = page.evaluate(_TOC_INJECT_JS, display_pages)
    logger.info("目录页码注入: %d/%d 项", injected, len(display_pages))
    final_bytes = page.pdf(**pass1_kwargs)
    final_bytes = apply_progress_rail(final_bytes, toc_pages)
    pdf_path.write_bytes(final_bytes)


def _generate_pdf_impl(html: str, *, header_meta: dict | None = None) -> Path:
    """实际的 PDF 生成逻辑 (原 generate_pdf 主体)。

    Args:
        html: 完整 HTML 字符串。
        header_meta: 页眉页脚数据 (可选)。包含:
            - student_display_name: 学生姓名
            - report_title: 报告标题
            - report_date: 报告日期

    Returns:
        PDF 临时文件路径 (调用方负责清理)。

    Raises:
        RuntimeError: Playwright 未安装或浏览器启动失败。
    """
    browser = _get_browser()
    page = browser.new_page()
    page.set_default_timeout(900_000)  # 900s, 从实际执行开始计
    try:
        page.set_content(html, wait_until="networkidle")
        result = page.evaluate(_PREFLIGHT_JS)
        logger.info("预分页完成: %s", result)

        pdf_path = _create_temp_pdf_path()
        pdf_kwargs = _build_service_pdf_kwargs(pdf_path, header_meta)
        _write_pdf_with_toc(page, pdf_path, pdf_kwargs)

        logger.info("PDF 生成完成: %s (%d bytes)", pdf_path, pdf_path.stat().st_size)
        return pdf_path
    finally:
        page.close()


# ---------------------------------------------------------------------------
# 关闭
# ---------------------------------------------------------------------------

def shutdown():
    """关闭 Playwright 浏览器 + 专用线程池，FastAPI lifespan 关闭时调用。"""
    global _browser, _pw_context

    _pdf_executor.shutdown(wait=False)

    with _browser_lock:
        if _browser is not None:
            try:
                _browser.close()
                logger.info("Chromium 浏览器已关闭")
            except Exception:
                logger.exception("关闭浏览器失败")
            _browser = None

        if _pw_context is not None:
            try:
                _pw_context.stop()
            except Exception:
                logger.exception("关闭 Playwright context 失败")
            _pw_context = None
