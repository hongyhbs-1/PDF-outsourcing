#!/usr/bin/env python3
"""
独立渲染脚本 — 外包专用

用法:
    # 只生成 HTML
    python render_standalone.py samples/json/sample_01_math_25q.json -o output.html

    # 生成 HTML + PDF (需要 playwright)
    python render_standalone.py samples/json/sample_01_math_25q.json -o output.html --pdf

依赖:
    pip install jinja2
    pip install playwright  # 仅 PDF 需要
    playwright install chromium  # 或用系统 Chrome: 脚本自动尝试
    pip install PyMuPDF  # 可选, 用于目录页码注入
"""

import argparse
import json
from pathlib import Path

from adapters import adapt_payload
from renderer import (
    render_html,
    REPORT_VARIANTS,
    PARENT_REPORT_VARIANT,
    ADMISSIONS_BLUEPRINT_VARIANT,
)
from pdf_generator import generate_pdf

try:
    from golden_typeset.engine import build_typeset_css
    _HAS_GOLDEN = True
except ImportError:
    try:
        from scripts.golden_typeset.engine import build_typeset_css
        _HAS_GOLDEN = True
    except ImportError:
        _HAS_GOLDEN = False


def main():
    parser = argparse.ArgumentParser(description="报告渲染 (外包独立使用)")
    parser.add_argument("json_file", help="render_payload JSON 文件路径")
    parser.add_argument("-o", "--output", default="output.html", help="输出 HTML 路径")
    parser.add_argument("--pdf", action="store_true", help="同时生成 PDF")
    parser.add_argument(
        "--landscape", action="store_true", help="PDF/HTML 使用 A4 横版排版"
    )
    parser.add_argument(
        "--report-variant",
        choices=sorted(REPORT_VARIANTS),
        default=PARENT_REPORT_VARIANT,
        help="输出版本：parent=家长版主报告；admissions_blueprint=招生老师学习蓝图；full=旧版完整报告",
    )
    args = parser.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as f:
        payload = adapt_payload(json.load(f))

    typeset_css = ""
    if _HAS_GOLDEN:
        typeset_css = build_typeset_css(payload)

    landscape = bool(
        args.landscape or args.report_variant == ADMISSIONS_BLUEPRINT_VARIANT
    )
    html = render_html(
        payload,
        typeset_css=typeset_css,
        report_variant=args.report_variant,
        landscape=landscape,
    )
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"HTML: {args.output}")

    if args.pdf:
        pdf_path = args.output.replace(".html", ".pdf")
        generate_pdf(
            pdf_path, payload, report_variant=args.report_variant, landscape=landscape
        )


if __name__ == "__main__":
    main()
