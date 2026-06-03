"""HTML 渲染服务 — RenderPayload -> 完整 HTML。

.. deprecated::
    此模块为 templates_v2 时代遗留，仅供 v2 管线内部使用。
    新功能请使用 ``renderer.py`` 中的 ``render_html()``。

CSS 拼接 (base.css + m*.css) 和 Jinja2 渲染逻辑从
templates_v2/_scripts/render_smoke_test.py 和 tests_v2/test_e2e_render.py 提取。

用法:
    from src_v2.services.html_renderer import render_html
    html = render_html(payload, for_pdf=False)
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import jinja2

try:
    from golden_typeset.engine import build_typeset_css
    _HAS_GOLDEN = True
except ImportError:
    try:
        from scripts.golden_typeset.engine import build_typeset_css
        _HAS_GOLDEN = True
    except ImportError:
        _HAS_GOLDEN = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_TEMPLATES_DIR = _PROJECT_ROOT / "templates_v2"
_CSS_DIR = _TEMPLATES_DIR / "css"
_FONTS_DIR = _TEMPLATES_DIR / "fonts"

# ---------------------------------------------------------------------------
# 模块级缓存
# ---------------------------------------------------------------------------

_combined_css: str | None = None
_jinja_env: jinja2.Environment | None = None


def _load_combined_css() -> str:
    """读取并拼接 base.css + m*.css，结果缓存。"""
    global _combined_css
    if _combined_css is not None:
        return _combined_css

    parts: list[str] = []
    base = _CSS_DIR / "base.css"
    if base.exists():
        parts.append(base.read_text(encoding="utf-8"))
    for css_file in sorted(_CSS_DIR.glob("m*.css")):
        parts.append(css_file.read_text(encoding="utf-8"))

    _combined_css = "\n".join(parts)
    logger.info("CSS 拼接完成: %d 字符, %d 文件", len(_combined_css), len(parts))
    return _combined_css


def _get_jinja_env() -> jinja2.Environment:
    """创建 Jinja2 环境，结果缓存。"""
    global _jinja_env
    if _jinja_env is not None:
        return _jinja_env

    _jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        undefined=jinja2.Undefined,  # 宽松模式，允许降级
        autoescape=True,
    )
    return _jinja_env


# ---------------------------------------------------------------------------
# 字体路径重写 (PDF 模式)
# ---------------------------------------------------------------------------

_FONT_RELATIVE_PATTERN = re.compile(
    r"""url\(\s*['"]?\.\./fonts/NotoSansSC-Variable\.ttf['"]?\s*\)"""
)


def _rewrite_font_paths(css: str) -> str:
    """将 CSS 中的相对字体路径替换为 file:// 绝对路径 (Playwright PDF 需要)。"""
    font_file = _FONTS_DIR / "NotoSansSC-Variable.ttf"
    if not font_file.exists():
        logger.warning("字体文件不存在: %s, 跳过路径重写", font_file)
        return css
    absolute_uri = font_file.as_uri()
    return _FONT_RELATIVE_PATTERN.sub(f"url('{absolute_uri}')", css)


# ---------------------------------------------------------------------------
# 调试辅助函数
# ---------------------------------------------------------------------------

def _save_render_payload_debug(context: dict) -> None:
    """保存渲染 payload 到 JSON 文件用于调试。

    Args:
        context: 传递给 jinja2 模板的渲染上下文
    """
    # 可通过环境变量控制是否保存（默认保存）
    if os.getenv("DISABLE_RENDER_PAYLOAD_DEBUG", "").lower() in ("1", "true", "yes"):
        return

    logs_dir = _PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    debug_file = logs_dir / f"render_payload_debug_{timestamp}.json"

    try:
        # 移除 combined_css 以减小文件大小（CSS 内容较大）
        debug_context = dict(context)
        debug_context.pop("combined_css", None)

        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(debug_context, f, ensure_ascii=False, indent=2)
        logger.info("渲染 payload 已保存到: %s", debug_file)
    except Exception as e:
        logger.warning("保存渲染 payload 失败: %s", e)


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def _build_page_visibility(payload: dict, config: dict | None,
                           report_type: str) -> dict:
    """收敛所有页面可见性判断到一处。"""
    pv = {}
    if config:
        pv = dict(config.get("page_visibility", {}))
        features = config.get("features", {})
        if not features.get("enable_city_compare", True):
            pv["m5_city_compare"] = False

    if report_type != "teacher":
        pv["show_teacher_supplement"] = False
    else:
        pv["show_teacher_supplement"] = bool(payload.get("teacher_supplement"))

    pv.setdefault("m5_city_compare", True)
    pv.setdefault("m9_question_detail", True)
    pv.setdefault("m10_composition", False)
    pv.setdefault("show_teacher_supplement", False)
    return pv


def render_html(payload: dict, *, for_pdf: bool = False,
                report_type: str = "main",
                config: dict | None = None) -> str:
    """将 RenderPayload 渲染为完整 HTML 字符串。

    Args:
        payload: S5 产出的 RenderPayload 字典。
        for_pdf: True 时将 CSS 字体路径重写为 file:// 绝对路径。
        report_type: "main" (学生/家长版) 或 "teacher" (教师版, 含 teacher_supplement)。
        config: yaml 配置 (含 page_visibility/features), None 时使用默认可见性。

    Returns:
        完整 HTML 字符串 (<!DOCTYPE html>...)。
    """
    css = _load_combined_css()

    # 黄金比例布局: 计算并注入排版 CSS
    if _HAS_GOLDEN:
        css = css + build_typeset_css(payload)

    if for_pdf:
        css = _rewrite_font_paths(css)

    context = dict(payload)
    context["combined_css"] = css
    # 兼容远端工程师模板: 模板中同时支持 render_payload.xxx 和直接变量访问
    context["render_payload"] = payload

    # 模板变量别名: 工程师模板使用 section_xxx 命名，我们管线输出为 module 名
    context.setdefault("section_core_weakness", payload.get("core_weakness", {}))
    context.setdefault("section_2_domains", payload.get("domains", {}))

    # 调试：保存渲染 payload 到 JSON 文件
    _save_render_payload_debug(context)

    # 调试：打印 breakthrough 字段的详细信息
    bt = context.get("breakthrough", {})
    logger.debug("DEBUG: breakthrough type=%s, keys=%s, items type=%s",
                type(bt).__name__,
                list(bt.keys()) if isinstance(bt, dict) else "N/A",
                type(bt.get("items")).__name__ if bt.get("items") is not None else "None")
    if bt.get("items"):
        logger.debug("DEBUG: bt_items[0] type=%s, value=%s",
                    type(bt.get("items")[0]) if bt.get("items") else "N/A",
                    str(bt.get("items")[0])[:200] if bt.get("items") else "N/A")

    # E1-FINAL: 双报告类型标记 + 页面可见性
    context["report_type"] = report_type
    context["is_teacher_report"] = report_type == "teacher"
    context["page_visibility"] = _build_page_visibility(payload, config, report_type)

    env = _get_jinja_env()
    template = env.get_template("report_master.jinja2")
    html = template.render(**context)
    logger.info("HTML 渲染完成: %d 字符, for_pdf=%s, report_type=%s",
                len(html), for_pdf, report_type)
    return html
