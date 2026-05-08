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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Playwright 可用性检测
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright, Browser
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    import fitz  # PyMuPDF — 目录页码提取
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

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
# 预分页: 名单制处理高风险块
# ---------------------------------------------------------------------------

_PREFLIGHT_JS = """
() => {
    // ─── M3: 取消强制分页，避免空白页 ───
    // 注释掉强制分页逻辑，让 Playwright 自然处理分页
    // 这样可以避免内容很少的面板导致空白页的问题
    /*
    const panels = document.querySelectorAll('.m3-kp-drill__panel');
    let firstNonEmpty = true;
    panels.forEach(panel => {
        const dataRows = panel.querySelectorAll('tbody tr');
        if (dataRows.length > 0) {
            if (!firstNonEmpty) {
                panel.style.breakBefore = 'page';
            }
            firstNonEmpty = false;
        }
    });
    */

    // ─── M5: 强制清理 (belt-and-suspenders, CSS 应已修复) ───
    const m5 = document.querySelector('.m5-city-compare');
    if (m5) {
        m5.style.minHeight = 'auto';
        m5.style.pageBreakInside = 'auto';
    }

    // ─── M1: 放松 breakthrough-grid 整体 avoid (CSS 应已修复) ───
    const btGrid = document.querySelector('.m1-breakthrough-grid');
    if (btGrid) {
        btGrid.style.breakInside = 'auto';
    }

    // ─── M7: 置信度说明不独占页 ───
    document.querySelectorAll('.m7-note').forEach(note => {
        note.style.breakInside = 'auto';
        note.style.pageBreakInside = 'auto';
    });

    // ─── M8: 避免最后一个面板跨页导致的空白页 ───
    // 让最后一个面板允许跨页，避免最后一页只剩页眉页脚
    // 使用 :last-of-type 而不是 :last-child 以正确选择最后一个 section
    const lastM8Panel = document.querySelector('.m8-appendix-panel:last-of-type');
    if (lastM8Panel) {
        lastM8Panel.style.breakInside = 'auto';
        lastM8Panel.style.pageBreakInside = 'auto';
    }

    // ─── 全局: 避免每个模块最后一个元素导致空白页 ───
    // 让每个模块的最后一个 card/panel/table 等元素允许跨页
    const modulePages = document.querySelectorAll('.module-page');
    modulePages.forEach(page => {
        // 查找每个模块内的最后一个可能跨页的元素
        const lastElements = page.querySelectorAll('.card, .kp-card, .domain-card, .breakthrough-card, .m8-appendix-panel, .m7-note, table');
        if (lastElements.length > 0) {
            const lastEl = lastElements[lastElements.length - 1];
            lastEl.style.breakInside = 'auto';
            lastEl.style.pageBreakInside = 'auto';
        }
    });

    // ─── [FIX] 避免中间空白页: 检测内容少的模块，移除强制分页 ───
    // 计算页面高度（A4: ~297mm，在 96DPI 下约 1123px）
    // 页面可打印区域（减去页眉页脚）约 900-1000px
    const MAX_CONTENT_HEIGHT = 900; // px
    const MIN_CONTENT_HEIGHT = 300;  // px

    modulePages.forEach((page, index) => {
        // 跳过第一个模块和漫画模块
        if (index === 0 || page.classList.contains('comic-module')) {
            return;
        }

        const height = page.getBoundingClientRect().height;

        // 如果模块高度小于最大值且大于最小值，允许它跨页
        // 这样可以避免内容很少的模块单独占一页
        if (height < MAX_CONTENT_HEIGHT && height > MIN_CONTENT_HEIGHT) {
            page.style.breakBefore = 'auto';
            page.style.pageBreakBefore = 'auto';
        }
    });

    // ─── 全局: 放松所有 >200px 块的 break-inside:avoid ───
    const THRESHOLD = 200;
    const avoidSelectors = [
        '.m1-suggestion-callout',
        '.m2-cw-tips-box',
        '.m4-chart-box',
        '.m4-summary-card',
    ];
    avoidSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            const h = el.getBoundingClientRect().height;
            if (h > THRESHOLD) {
                el.style.breakInside = 'auto';
                el.style.pageBreakInside = 'auto';
            }
        });
    });

    return {
        panels_total: document.querySelectorAll('.m3-kp-drill__panel').length,
        panels_with_data: [...document.querySelectorAll('.m3-kp-drill__panel')]
            .filter(p => p.querySelectorAll('tbody tr').length > 0).length,
        m5_fixed: !!m5,
        relaxed_blocks: avoidSelectors.length,
    };
}
"""


def _preflight_paginate(page) -> dict:
    """在 page.pdf() 之前运行, 修正高风险分页点。

    名单制处理:
      - M3: 已取消强制分页，避免内容很少的面板导致空白页（让 Playwright 自然处理）
      - M5: 清除 min-height:297mm + page-break-inside:avoid
      - M1: 放松 breakthrough-grid 整体 break-inside:avoid
      - M7: 放松置信度说明 break-inside
      - M8: 避免最后一个面板导致最后一页空白
      - 全局: 每个模块最后一个元素允许跨页，避免空白最后一页
      - 通用: >200px 的高风险尾块放松 break-inside:avoid

    Returns:
        预检统计信息 (用于日志)。
    """
    result = page.evaluate(_PREFLIGHT_JS)
    logger.info("预分页完成: %s", result)
    return result


# ---------------------------------------------------------------------------
# 两次渲染: 目录页码提取 + 注入
# ---------------------------------------------------------------------------

# 章节标题搜索标记 → TOC key (PDF 文本匹配用)
# 注: TOC 页使用 "一" (无顿号), 模块标题使用 "一、" (有顿号), 不会误匹配
_TOC_SEARCH_MAP: list[tuple[str, str]] = [
    ("m1", "一、"),
    ("m4", "二、"),
    ("m2", "三、"),
    ("m3", "四、"),
    ("m5", "五、"),
    ("m6", "六、"),
    ("m9", "七、"),
    ("m7", "八、"),
    ("m8", "分析范围"),  # m8 标题 fitz 无法提取, 用首个面板标题代替
    ("m10", "十、"),
    ("m11", "十一、"),
]
_TOC_DISPLAY_KEYS = {"m1", "m4", "m2", "m3", "m5", "m6", "m9", "m7", "m8"}


def _extract_toc_pages(pdf_bytes: bytes) -> dict[str, int]:
    """从 PDF 二进制内容中提取各章节起始页码。

    按中文序号 "一、"~"七、" + "附录：" 在 PDF 文本中定位首次出现的页码。

    Returns:
        {"m1": 4, "m4": 6, ...} (1-based 页码)。
        fitz 不可用或未找到任何章节时返回空 dict。
    """
    if not HAS_FITZ:
        logger.warning("PyMuPDF (fitz) 未安装, 跳过目录页码提取")
        return {}

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result: dict[str, int] = {}
    found_keys: set[str] = set()

    for page_idx in range(len(doc)):
        text = doc[page_idx].get_text()
        for key, marker in _TOC_SEARCH_MAP:
            if key not in found_keys and marker in text:
                result[key] = page_idx + 1  # 1-based
                found_keys.add(key)
        if len(found_keys) == len(_TOC_SEARCH_MAP):
            break  # 全部找到, 提前退出

    doc.close()
    logger.info("目录页码提取: %s", result)
    return result


def _toc_pages_for_injection(toc_pages: dict[str, int]) -> dict[str, int]:
    return {
        key: page_number
        for key, page_number in toc_pages.items()
        if key in _TOC_DISPLAY_KEYS
    }


_TOC_INJECT_JS = """
(toc_pages) => {
    let injected = 0;
    for (const [key, pageNum] of Object.entries(toc_pages)) {
        const el = document.querySelector(`[data-toc-key="${key}"]`);
        if (el) {
            el.textContent = String(pageNum);
            injected++;
        }
    }
    return injected;
}
"""


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
        _preflight_paginate(page)

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
