"""Shared Playwright PDF header and footer templates."""

from __future__ import annotations

from functools import lru_cache
import html
from pathlib import Path
from typing import Any


TEXT_MUTED = "#6B7A86"
TEXT_STRONG = "#12344D"
TEAL = "#1F6F78"
TEAL_SOFT = "#D0E8E8"
SAND = "#D9B36A"
LINE = "#DDE5E8"

MARGIN_TOP = "12mm"
MARGIN_BOTTOM = "10mm"
MARGIN_LEFT = "0mm"
MARGIN_RIGHT = "0mm"

HEADER_PADDING = "6.6mm 15mm 0 18mm"
FOOTER_PADDING = "0 15mm 5.4mm 18mm"
DEFAULT_TITLE = "学情诊断报告"
DEFAULT_BRAND = "dida985小程序"
DEFAULT_POSITIONING = "逐题透析 · 逐点拆解 · 对标历年真题考点"
FONT_FILE = Path(__file__).resolve().parent.parent / "templates" / "fonts" / "NotoSansSC-Variable.ttf"


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _meta_value(meta: dict | None, *keys: str, default: str = "") -> str:
    if not meta:
        return default
    for key in keys:
        value = meta.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _build_header_context(meta: dict | None) -> str:
    """Build the right-side PDF header context line."""
    explicit = _meta_value(meta, "header_meta_line")
    if explicit:
        return explicit

    student = _meta_value(meta, "student_display_name", "student_name")
    grade = _meta_value(meta, "grade", "student_grade")
    subject = _meta_value(meta, "subject_name", "subject", default="学科")
    target = _meta_value(meta, "target_score_text")

    parts = [part for part in [student, grade, subject] if part]
    if target:
        parts.append(f"目标 {target}")
    return " ｜ ".join(parts) if parts else DEFAULT_POSITIONING


@lru_cache(maxsize=1)
def _font_face_css() -> str:
    if not FONT_FILE.exists():
        return ""
    return (
        '@font-face {'
        'font-family: "Noto Sans SC";'
        'src: local("Noto Sans SC"),'
        f"url('{FONT_FILE.as_uri()}') format('truetype');"
        'font-weight: 100 900;'
        'font-style: normal;'
        '}'
    )


def _base_style() -> str:
    return f"""<style>
{_font_face_css()}
#header, #footer {{
  margin: 0 !important;
  box-sizing: border-box !important;
  width: 100% !important;
  background: transparent !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}}
#header {{ padding: 0 !important; }}
#footer {{ padding: 0 !important; }}
.pw-hf-wrap {{
  width: 100%;
  box-sizing: border-box;
  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
}}
.pw-hf-row {{
  width: 100%;
  display: flex;
  align-items: center;
  box-sizing: border-box;
  color: {TEXT_MUTED};
  font-size: 8px;
  line-height: 1;
}}
.pw-hf-ellipsis {{
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.pw-hf-pill {{
  border-radius: 999px;
  background: {TEAL_SOFT};
  color: {TEXT_STRONG};
  padding: 1.2mm 3.2mm;
}}
</style>"""


def build_pdf_margins() -> dict[str, str]:
    return {
        "top": MARGIN_TOP,
        "bottom": MARGIN_BOTTOM,
        "left": MARGIN_LEFT,
        "right": MARGIN_RIGHT,
    }


def build_header_template(meta: dict | None) -> str:
    title = _escape(_meta_value(meta, "report_short_title", "report_title", default=DEFAULT_TITLE))
    context_text = _escape(_build_header_context(meta))

    return (
        _base_style()
        + f'<div class="pw-hf-wrap" style="height:{MARGIN_TOP}; padding:{HEADER_PADDING};">'
        + '  <div class="pw-hf-row" style="height:5mm; border-bottom:0.5px solid '
        + f'{LINE}; padding-bottom:1.1mm;">'
        + f'    <span class="pw-hf-ellipsis" style="flex:0 0 38%; color:{TEXT_STRONG};">{title}</span>'
        + f'    <span class="pw-hf-ellipsis" style="flex:1; text-align:right; color:{TEAL};">{context_text}</span>'
        + '  </div>'
        + f'  <div style="width:18mm; height:0.6mm; background:{SAND}; margin-top:-0.3mm;"></div>'
        + '</div>'
    )


def build_footer_template(meta: dict | None) -> str:
    title = _escape(_meta_value(meta, "report_title", "report_name", default=DEFAULT_TITLE))
    report_date = _escape(_meta_value(meta, "report_date", "date"))
    brand = _escape(_meta_value(meta, "brand_name", default=DEFAULT_BRAND))
    date_text = f"报告日期：{report_date}" if report_date else ""

    return (
        _base_style()
        + f'<div class="pw-hf-wrap" style="height:{MARGIN_BOTTOM}; padding:{FOOTER_PADDING};'
        + ' display:flex; align-items:flex-end;">'
        + f'  <div class="pw-hf-row" style="height:4.6mm; border-top:0.5px solid {LINE}; padding-top:1mm;">'
        + f'    <span class="pw-hf-ellipsis" style="flex:1;">{brand} · {title}</span>'
        + '    <span class="pw-hf-pill" style="flex:0 0 auto;">'
        + '第 <span class="pageNumber"></span> / <span class="totalPages"></span> 页'
        + '    </span>'
        + f'    <span class="pw-hf-ellipsis" style="flex:1; text-align:right;">{date_text}</span>'
        + '  </div>'
        + '</div>'
    )


def build_pdf_chrome_options(meta: dict | None) -> dict[str, object]:
    return {
        "display_header_footer": True,
        "margin": build_pdf_margins(),
        "header_template": build_header_template(meta),
        "footer_template": build_footer_template(meta),
    }
