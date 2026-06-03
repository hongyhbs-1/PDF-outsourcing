#!/usr/bin/env python3
"""PDF 阅读进度边条回归测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

import fitz

import pdf_progress_rail as rail


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_UTILS = PROJECT_ROOT / "scripts" / "pdf_utils.py"
PDF_SERVICE = PROJECT_ROOT / "scripts" / "pdf_service.py"


class PdfProgressRailTest(unittest.TestCase):
    def make_blank_pdf(self, page_count: int) -> bytes:
        doc = fitz.open()
        for _ in range(page_count):
            doc.new_page(width=595, height=842)
        source = doc.tobytes()
        doc.close()
        return source

    def test_build_section_ranges_from_toc_pages(self) -> None:
        toc_pages = {"m1": 3, "m4": 5, "m2": 7}

        ranges = rail.build_section_ranges(toc_pages, total_pages=10)

        self.assertEqual(["m1", "m4", "m2"], [item.key for item in ranges])
        self.assertEqual((3, 4), (ranges[0].start_page, ranges[0].end_page))
        self.assertEqual((5, 6), (ranges[1].start_page, ranges[1].end_page))
        self.assertEqual((7, 10), (ranges[2].start_page, ranges[2].end_page))

    def test_section_for_page_returns_none_before_first_section(self) -> None:
        ranges = rail.build_section_ranges({"m1": 3, "m4": 5}, total_pages=8)

        self.assertIsNone(rail.section_for_page(1, ranges))
        self.assertIsNone(rail.section_for_page(2, ranges))
        self.assertEqual("m1", rail.section_for_page(3, ranges).key)
        self.assertEqual("m4", rail.section_for_page(8, ranges).key)

    def test_build_section_ranges_rejects_invalid_pages(self) -> None:
        with self.assertRaises(ValueError):
            rail.build_section_ranges({"m1": 0}, total_pages=8)

        with self.assertRaises(ValueError):
            rail.build_section_ranges({"m1": 9}, total_pages=8)

    def test_apply_progress_rail_preserves_page_count(self) -> None:
        source = self.make_blank_pdf(4)

        output = rail.apply_progress_rail(source, {"m1": 2, "m4": 3})
        output_doc = fitz.open(stream=output, filetype="pdf")

        self.assertEqual(4, len(output_doc))
        self.assertNotEqual(source, output)
        output_doc.close()

    def test_progress_rail_links_are_global_and_jump_to_section_pages(self) -> None:
        source = self.make_blank_pdf(4)

        output = rail.apply_progress_rail(source, {"m1": 2, "m4": 3})
        output_doc = fitz.open(stream=output, filetype="pdf")
        first_page_links = output_doc[0].get_links()
        second_page_links = output_doc[1].get_links()

        # Link insertion disabled (click-to-jump turned off)
        self.assertEqual([], first_page_links)
        self.assertEqual([], second_page_links)
        output_doc.close()

    def test_navigation_starts_from_first_section_page(self) -> None:
        source = self.make_blank_pdf(5)

        output = rail.apply_progress_rail(source, {"m1": 3, "m4": 4, "m2": 5})
        output_doc = fitz.open(stream=output, filetype="pdf")

        for page in output_doc[:2]:
            self.assertEqual([], page.get_links())

        # Link insertion disabled; verify pages after start still have no links
        for page in output_doc[2:]:
            goto_links = [
                link for link in page.get_links()
                if link["kind"] == fitz.LINK_GOTO
            ]
            self.assertEqual(0, len(goto_links))
        output_doc.close()

    def test_pdf_entries_apply_progress_rail_after_toc_extraction(self) -> None:
        standalone = PDF_UTILS.read_text(encoding="utf-8")
        service = PDF_SERVICE.read_text(encoding="utf-8")

        self.assertIn("from pdf_progress_rail import apply_progress_rail", standalone)
        self.assertIn("apply_progress_rail(final_bytes, toc_pages)", standalone)
        self.assertIn("from pdf_progress_rail import apply_progress_rail", service)
        self.assertIn("apply_progress_rail(final_bytes, toc_pages)", service)


if __name__ == "__main__":
    unittest.main()
