#!/usr/bin/env python3
"""
HTML 渲染核心 — CSS 合并 + Jinja2 模板渲染

从 render_standalone.py 拆分出的渲染逻辑。
"""

import base64
import math
from pathlib import Path

from learning_blueprint_builder import build_learning_blueprints

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    raise ImportError("请安装 jinja2: pip install jinja2")

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = PROJECT_DIR / "templates"
CSS_DIR = TEMPLATE_DIR / "css"
PAGES_DIR = TEMPLATE_DIR / "pages"
FONTS_DIR = TEMPLATE_DIR / "fonts"
ASSETS_DIR = TEMPLATE_DIR / "assets"
TIER_NEED_MAJOR_MAX = 60
TIER_ROOM_GROW_MAX = 85

# ---------------------------------------------------------------------------
# 报告变体常量
# ---------------------------------------------------------------------------

PARENT_REPORT_VARIANT = "parent"
ADMISSIONS_BLUEPRINT_VARIANT = "admissions_blueprint"
FULL_REPORT_VARIANT = "full"
REPORT_VARIANTS = {
    PARENT_REPORT_VARIANT,
    ADMISSIONS_BLUEPRINT_VARIANT,
    FULL_REPORT_VARIANT,
}

_LANDSCAPE_PRINT_CSS = """
/* Landscape PDF output: used by the standalone admissions/scene renderer. */
@page {
  size: A4 landscape;
}

@page english-report {
  size: A4 landscape;
}

:root {
  --page-width: 297mm;
  --page-min-height: 210mm;
  --page-print-height: 188mm;
  --landscape-content-zoom: 0.70;
}

@media screen {
  .learning-blueprint-page {
    width: var(--page-width);
    min-height: var(--page-print-height);
  }
}

@media print {
  .learning-blueprint-page {
    width: auto;
    min-height: var(--page-print-height);
    height: var(--page-print-height);
    padding: 5mm 7mm 4mm;
    overflow: hidden;
  }

  .learning-blueprint-page__scale {
    width: calc(100% / var(--landscape-content-zoom));
    transform: scale(var(--landscape-content-zoom));
    transform-origin: top left;
  }
}
"""


# ---------------------------------------------------------------------------
# 变体验证
# ---------------------------------------------------------------------------


def _validate_report_variant(report_variant: str) -> str:
    if report_variant not in REPORT_VARIANTS:
        allowed = ", ".join(sorted(REPORT_VARIANTS))
        raise ValueError(f"report_variant must be one of: {allowed}")
    return report_variant


# ---------------------------------------------------------------------------
# CSS 合并
# ---------------------------------------------------------------------------


def _rewrite_font_urls(css: str) -> str:
    """Rewrite bundled font URLs to absolute file URIs for PDF rendering."""
    font_file = FONTS_DIR / "NotoSansSC-Variable.ttf"
    if not font_file.exists():
        return css
    font_uri = font_file.resolve().as_uri()
    return css.replace("url('../fonts/NotoSansSC-Variable.ttf')", f"url('{font_uri}')")


def load_css() -> str:
    """合并所有 CSS 文件。

    加载顺序（visual_hierarchy.css 必须最后，确保层级 token 覆盖所有模块和 shared_*.css）：
    base.css → 按字母序其余 CSS → shared_*.css → visual_hierarchy.css
    """
    css_parts: list[str] = []
    base = CSS_DIR / "base.css"
    if base.exists():
        css_parts.append(base.read_text(encoding="utf-8"))
    # 按字母序加载所有非 base、非 shared、非 visual_hierarchy 的 CSS
    for f in sorted(CSS_DIR.glob("*.css")):
        if f.name == "base.css" or f.name.startswith("shared_") or f.name == "visual_hierarchy.css":
            continue
        css_parts.append(f.read_text(encoding="utf-8"))
    # 共享覆盖（shared_*.css）
    for f in sorted(CSS_DIR.glob("shared_*.css")):
        css_parts.append(f.read_text(encoding="utf-8"))
    # visual_hierarchy.css 最后加载 — 层级 token 必须是最终仲裁者
    vh = CSS_DIR / "visual_hierarchy.css"
    if vh.exists():
        css_parts.append(vh.read_text(encoding="utf-8"))
    return _rewrite_font_urls("\n".join(css_parts))


# ---------------------------------------------------------------------------
# 图片工具
# ---------------------------------------------------------------------------


def _image_to_data_uri(path: Path) -> str:
    """将本地图片文件转换为 data:image/...;base64,... Data URI。

    Playwright page.set_content() 创建 opaque origin, 无法加载 file:// 资源。
    将图片内嵌为 Data URI 可绕过此限制。
    """
    if not path.exists():
        return ""
    suffix_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }
    mime = suffix_map.get(path.suffix.lower(), "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# 等级选择
# ---------------------------------------------------------------------------


def _select_tier_name(payload: dict) -> str:
    """根据当前准确率选择漫画学生等级名。"""
    summary = payload.get("summary", {})
    acc = summary.get("current_accuracy", 0)

    if acc < TIER_NEED_MAJOR_MAX:
        return "差生"
    if acc < TIER_ROOM_GROW_MAX:
        return "中等生"
    return "优等生"


# ---------------------------------------------------------------------------
# 难度分布饼图 (m_overview.jinja2 消费)
# ---------------------------------------------------------------------------

_PIE_CX = 60.0
_PIE_CY = 60.0
_PIE_R = 50.0
_DIFFICULTY_LEVELS = {"easy", "medium", "hard"}


def _safe_float(value) -> float:
    if isinstance(value, str):
        value = value.strip().rstrip("%")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _pie_point(angle_deg: float) -> tuple:
    angle = math.radians(angle_deg)
    return (
        _PIE_CX + _PIE_R * math.cos(angle),
        _PIE_CY + _PIE_R * math.sin(angle),
    )


def _compute_difficulty_slices(payload: dict) -> list:
    """Build SVG pie slices for m_overview.jinja2."""
    appendix = payload.get("appendix") if isinstance(payload, dict) else None
    if not isinstance(appendix, dict):
        return []
    difficulty = appendix.get("difficulty")
    if not isinstance(difficulty, dict):
        return []
    items = difficulty.get("items")
    if not isinstance(items, list):
        return []

    entries = []
    for item in items:
        if not isinstance(item, dict):
            continue
        level = str(item.get("level") or "medium").strip().lower()
        if level not in _DIFFICULTY_LEVELS:
            level = "medium"
        ratio = max(0.0, _safe_float(item.get("ratio")))
        count = max(0.0, _safe_float(item.get("count")))
        entries.append({"level": level, "ratio": ratio, "count": count})

    ratio_total = sum(e["ratio"] for e in entries)
    count_total = sum(e["count"] for e in entries)
    weight_key = "ratio" if ratio_total > 0 else "count"
    total_weight = ratio_total if ratio_total > 0 else count_total
    if total_weight <= 0:
        return []

    positive = [e for e in entries if e[weight_key] > 0]
    if not positive:
        return []

    if len(positive) == 1:
        return [{"level": positive[0]["level"], "path_d": "", "full": True}]

    slices = []
    cumulative = 0.0
    last_index = len(positive) - 1
    for index, entry in enumerate(positive):
        weight = entry[weight_key]
        start_frac = cumulative / total_weight
        cumulative += weight
        end_frac = 1.0 if index == last_index else cumulative / total_weight
        sweep_angle = (end_frac - start_frac) * 360.0

        if sweep_angle >= 359.999:
            slices.append({"level": entry["level"], "path_d": "", "full": True})
            continue

        start_angle = start_frac * 360.0 - 90.0
        end_angle = end_frac * 360.0 - 90.0
        x1, y1 = _pie_point(start_angle)
        x2, y2 = _pie_point(end_angle)
        large_arc = 1 if sweep_angle > 180.0 else 0

        path_d = (
            f"M {_PIE_CX:g} {_PIE_CY:g} "
            f"L {x1:.3f} {y1:.3f} "
            f"A {_PIE_R:g} {_PIE_R:g} 0 {large_arc} 1 {x2:.3f} {y2:.3f} "
            "Z"
        )
        slices.append({"level": entry["level"], "path_d": path_d, "full": False})

    return slices


# ---------------------------------------------------------------------------
# 核心: HTML 渲染
# ---------------------------------------------------------------------------


def render_html(
    payload: dict,
    typeset_css: str = "",
    report_variant: str = PARENT_REPORT_VARIANT,
    landscape: bool = False,
) -> str:
    """将 JSON payload 渲染为 HTML。

    payload 应已由调用方通过 adapt_payload() 适配。

    report_variant:
      - parent: 家长版主报告，不包含两页复杂学习蓝图。
      - admissions_blueprint: 只渲染两页学习蓝图，供招生老师单独使用。
      - full: 兼容旧版完整报告，包含学习蓝图和主报告。
    """
    report_variant = _validate_report_variant(report_variant)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report_master.jinja2")

    font_path = FONTS_DIR / "NotoSansSC-Variable.ttf"
    logo_path = ASSETS_DIR / "logo_dida985.png"

    context = dict(payload)
    orientation_css = _LANDSCAPE_PRINT_CSS if landscape else ""
    context["combined_css"] = load_css() + orientation_css + typeset_css
    context["render_payload"] = payload
    context["report_variant"] = report_variant
    context.update(build_learning_blueprints(payload))
    context["font_path"] = str(font_path)
    context["logo_path"] = _image_to_data_uri(logo_path)
    # Kept for compatibility with older templates/debug output. Opening comic
    # pages are now replaced by the dynamic learning blueprint pages.
    context["tier_name"] = _select_tier_name(payload)
    context["overview_difficulty_slices"] = _compute_difficulty_slices(payload)

    # M9 逐题分析拆分
    try:
        from m9_splitter import has_m9_detail, build_m9_split_pages
        context["_has_m9_detail"] = has_m9_detail(payload)
        context["_m9_split_pages"] = build_m9_split_pages(payload)
    except ImportError:
        context["_has_m9_detail"] = False
        context["_m9_split_pages"] = []

    # 将封面 logo 路径也转为 Data URI (同因: page.set_content() 无法加载 file://)
    logo_data_uri = _image_to_data_uri(logo_path)
    cover = context.get("cover", context.get("module_0_cover", {}))
    brand = cover.get("brand", {}) if isinstance(cover, dict) else {}
    if logo_data_uri and isinstance(brand, dict):
        brand["logo_url"] = logo_data_uri

    return template.render(**context)
