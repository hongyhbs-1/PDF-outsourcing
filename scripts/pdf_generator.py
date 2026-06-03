#!/usr/bin/env python3
"""
PDF 生成 — 双 Pass 精确排版 → PDF

从 render_standalone.py 拆分出的 PDF 生成入口。
"""

import sys
import tempfile
from pathlib import Path

from adapters import adapt_payload
from renderer import (
    render_html,
    PARENT_REPORT_VARIANT,
    ADMISSIONS_BLUEPRINT_VARIANT,
    _validate_report_variant,
)
from pdf_utils import (
    _ensure_fontconfig_env,
    _build_pdf_kwargs,
    _launch_chromium,
    _wait_for_images,
    _build_final_pdf_bytes,
)

try:
    from golden_typeset.payload_analyzer import measure_dom_heights
    from golden_typeset.engine import build_typeset_css
    _HAS_GOLDEN = True
except ImportError:
    try:
        from scripts.golden_typeset.payload_analyzer import measure_dom_heights
        from scripts.golden_typeset.engine import build_typeset_css
        _HAS_GOLDEN = True
    except ImportError:
        _HAS_GOLDEN = False


def generate_pdf(
    output_path: str,
    payload: dict,
    comic_image_root=None,
    report_variant: str = PARENT_REPORT_VARIANT,
    landscape: bool = False,
) -> Path:
    """双 Pass 精确排版 → PDF。

    report_variant 与 render_html 一致：家长版默认不包含学习蓝图；招生版只包含学习蓝图两页。

    Pass 1: 渲染 HTML → 测量 DOM 高度
    Pass 2: 用测量值生成排版 CSS → 渲染 HTML → 生成 PDF
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("PDF 生成需要 playwright: pip install playwright")
        sys.exit(1)

    report_variant = _validate_report_variant(report_variant)
    payload = adapt_payload(payload)
    landscape = bool(landscape or report_variant == ADMISSIONS_BLUEPRINT_VARIANT)
    _ensure_fontconfig_env()
    pdf_kwargs = _build_pdf_kwargs(payload, landscape=landscape)
    output = Path(output_path)

    temp_html_paths: list[Path] = []
    with sync_playwright() as p:
        browser = _launch_chromium(p)
        page = browser.new_page()

        def load_html_via_file(html: str) -> None:
            """Load HTML from file:// so bundled fonts resolve in Chromium PDF."""
            with tempfile.NamedTemporaryFile(
                "w",
                suffix=".html",
                encoding="utf-8",
                delete=False,
            ) as temp_html:
                temp_html.write(html)
                temp_path = Path(temp_html.name)
            temp_html_paths.append(temp_path)
            page.goto(temp_path.as_uri(), wait_until="load")

        try:
            # -- Pass 1: 测量 DOM 高度 --
            measured = {}
            if _HAS_GOLDEN:
                html_pass1 = render_html(
                    payload,
                    comic_image_root=comic_image_root,
                    report_variant=report_variant,
                    landscape=landscape,
                )
                load_html_via_file(html_pass1)
                page.emulate_media(media="print")
                try:
                    measured = measure_dom_heights(page)
                    print(f"[Pass 1] DOM 测量完成: {len(measured)} 个模块")
                except Exception as e:
                    print(f"[WARNING] Pass 1 DOM 测量失败, 回退到单 Pass 模式: {e}")
                    measured = {}

            # -- Pass 2: 精确排版 + PDF 生成 --
            typeset_css = ""
            if _HAS_GOLDEN and measured:
                typeset_css = build_typeset_css(payload, measured=measured)

            html_pass2 = render_html(
                payload,
                comic_image_root=comic_image_root,
                typeset_css=typeset_css,
                report_variant=report_variant,
                landscape=landscape,
            )
            load_html_via_file(html_pass2)
            _wait_for_images(page)

            final_bytes = _build_final_pdf_bytes(page, pdf_kwargs)
            output.write_bytes(final_bytes)

            print(f"PDF: {output} ({output.stat().st_size:,} bytes)")
        finally:
            page.close()
            browser.close()
            for temp_html_path in temp_html_paths:
                temp_html_path.unlink(missing_ok=True)

    return output
