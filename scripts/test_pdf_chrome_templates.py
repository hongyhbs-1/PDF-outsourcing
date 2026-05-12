#!/usr/bin/env python3
"""PDF 页眉页脚共享模板回归测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

import pdf_chrome_templates as chrome


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RENDER_STANDALONE = PROJECT_ROOT / "scripts" / "render_standalone.py"
PDF_SERVICE = PROJECT_ROOT / "scripts" / "pdf_service.py"


class PdfChromeTemplatesTest(unittest.TestCase):
    def test_build_pdf_chrome_options_contains_expected_fields(self) -> None:
        meta = {
            "student_display_name": "张小明",
            "subject_name": "数学",
            "report_title": "张小明的学情诊断报告",
            "report_date": "2026-04-30",
        }

        options = chrome.build_pdf_chrome_options(meta)

        self.assertTrue(options["display_header_footer"])
        self.assertEqual(chrome.build_pdf_margins(), options["margin"])
        self.assertIn("张小明", options["header_template"])
        self.assertIn("数学", options["header_template"])
        self.assertIn("张小明的学情诊断报告", options["footer_template"])
        self.assertIn("2026-04-30", options["footer_template"])
        self.assertIn("pageNumber", options["footer_template"])
        self.assertIn("totalPages", options["footer_template"])

    def test_templates_do_not_overlay_body_or_use_old_saturated_style(self) -> None:
        template = (
            chrome.build_header_template({}) +
            chrome.build_footer_template({})
        )

        self.assertNotIn("position:absolute", template)
        self.assertNotIn("position: absolute", template)
        self.assertNotIn("#5B9EA6", template)
        self.assertNotIn("background: #F9F9F9", template)

    def test_margins_match_header_footer_height(self) -> None:
        margins = chrome.build_pdf_margins()

        self.assertEqual("12mm", margins["top"])
        self.assertEqual("10mm", margins["bottom"])
        self.assertEqual("0mm", margins["left"])
        self.assertEqual("0mm", margins["right"])

    def test_pdf_entries_use_shared_helper(self) -> None:
        standalone = RENDER_STANDALONE.read_text(encoding="utf-8")
        service = PDF_SERVICE.read_text(encoding="utf-8")

        self.assertIn("from pdf_chrome_templates import", standalone)
        self.assertIn("build_pdf_chrome_options", standalone)
        self.assertIn("from pdf_chrome_templates import", service)
        self.assertIn("build_pdf_chrome_options", service)


if __name__ == "__main__":
    unittest.main()
