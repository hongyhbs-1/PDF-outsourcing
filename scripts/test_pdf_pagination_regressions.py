#!/usr/bin/env python3
"""分页回归测试。

覆盖 3 个已定位的空白页根因：
1. M8 附录不应再声明独立命名页。
2. improvement_preview 不应使用 margin-top:auto 将总结条推到新页。
3. render_all_samples 使用的 render_standalone 预分页逻辑不应按模块高度移除 break-before。
"""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
M8_CSS = PROJECT_ROOT / "templates" / "css" / "m8_appendix.css"
IP_CSS = PROJECT_ROOT / "templates" / "css" / "improvement_preview.css"
PDF_UTILS = PROJECT_ROOT / "scripts" / "pdf_utils.py"
BASE_CSS = PROJECT_ROOT / "templates" / "css" / "base.css"
COVER_CSS = PROJECT_ROOT / "templates" / "css" / "m0_cover.css"
M1_CSS = PROJECT_ROOT / "templates" / "css" / "m1_summary.css"
M1_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m1_summary.jinja2"
M2_CSS = PROJECT_ROOT / "templates" / "css" / "m2_core_weakness.css"
M4_CSS = PROJECT_ROOT / "templates" / "css" / "m4_domains.css"
M5_CSS = PROJECT_ROOT / "templates" / "css" / "m5_city_compare.css"
M6_CSS = PROJECT_ROOT / "templates" / "css" / "m6_tiered_learning.css"
M7_CSS = PROJECT_ROOT / "templates" / "css" / "m7_data_reliability.css"
M8_APPENDIX_CSS = PROJECT_ROOT / "templates" / "css" / "m8_appendix.css"
MOV_CSS = PROJECT_ROOT / "templates" / "css" / "m_overview.css"
M3_CSS = PROJECT_ROOT / "templates" / "css" / "m3_kp_drill.css"
M3_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m3_kp_drill.jinja2"
M10_CSS = PROJECT_ROOT / "templates" / "css" / "m10_composition.css"
M11_CSS = PROJECT_ROOT / "templates" / "css" / "m11_reading_deep.css"
M9_CSS = PROJECT_ROOT / "templates" / "css" / "m9_question_detail.css"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PdfPaginationRegressionTest(unittest.TestCase):
    def test_m8_appendix_does_not_use_named_page(self) -> None:
        css = read_text(M8_CSS)
        self.assertNotIn("@page appendix", css)
        self.assertNotIn("page: appendix;", css)

    def test_improvement_summary_is_not_auto_pushed_to_bottom(self) -> None:
        css = read_text(IP_CSS)
        self.assertNotIn("margin-top: auto;", css)

    def test_improvement_preview_print_uses_compact_block_flow(self) -> None:
        print_rules = read_text(IP_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".ip-page", print_rules)
        self.assertIn("display: block;", print_rules)
        self.assertIn("flex: none;", print_rules)
        self.assertIn(".ip-phase-grid", print_rules)
        self.assertIn("margin-bottom: 8px;", print_rules)

    def test_render_standalone_does_not_override_module_break_before_by_height(self) -> None:
        source = read_text(PDF_UTILS)
        # 旧的高度阈值常量已删除
        self.assertNotIn("MAX_CONTENT_HEIGHT", source)
        self.assertNotIn("MIN_CONTENT_HEIGHT", source)
        # 紧凑算法(密度驱动)合法使用 breakBefore/pageBreakBefore,
        # 但不允许基于固定像素高度的 break-before 覆盖
        self.assertNotIn("offsetHeight", source)

    def test_print_page_shell_does_not_depend_on_viewport_height(self) -> None:
        for path in (BASE_CSS, COVER_CSS):
            self.assertNotIn("100vh", read_text(path))

    def test_print_module_shell_uses_block_flow(self) -> None:
        css = read_text(BASE_CSS)
        print_rules = css.split("@media print", maxsplit=1)[1]
        self.assertIn("display: block;", print_rules)

    def test_m2_print_root_uses_block_flow(self) -> None:
        css = read_text(M2_CSS)
        print_rules = css.split("@media print", maxsplit=1)[1]
        self.assertIn(".m2-core-weakness-module", print_rules)
        self.assertIn("display: block;", print_rules)
        self.assertIn("flex: none;", print_rules)

    def test_m1_breakthrough_does_not_force_new_page(self) -> None:
        css = read_text(M1_CSS)
        self.assertNotIn("break-before: page;", css)
        self.assertNotIn("page-break-before: always;", css)

    def test_m1_dense_breakthrough_uses_compact_four_column_print_grid(self) -> None:
        template = read_text(M1_TEMPLATE)
        print_rules = read_text(M1_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn("m1-report-page--dense", template)
        self.assertIn(".m1-report-page--dense .m1-breakthrough-grid", print_rules)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", print_rules)
        self.assertIn(".m1-report-page--dense .m1-breakthrough-card", print_rules)

    def test_m4_large_containers_allow_natural_page_breaks(self) -> None:
        css = read_text(M4_CSS)
        self.assertIn("break-inside: auto;", css)
        self.assertIn("page-break-inside: auto;", css)

    def test_m5_city_compare_does_not_push_footnote_to_page_bottom(self) -> None:
        css = read_text(M5_CSS)
        self.assertNotIn("margin-top: auto;", css)

    def test_m5_print_root_uses_compact_block_flow(self) -> None:
        css = read_text(M5_CSS)
        print_rules = css.split("@media print", maxsplit=1)[1]
        self.assertIn(".m5-city-compare", print_rules)
        self.assertIn("display: block;", print_rules)
        self.assertIn("flex: none;", print_rules)
        self.assertIn("grid-template-columns: repeat(3, 1fr);", print_rules)
        self.assertIn("page-break-inside: auto;", print_rules)

    def test_late_long_modules_use_compact_print_flow(self) -> None:
        for path, selector in (
            (M6_CSS, ".m6-page"),
            (M7_CSS, ".m7-data-reliability"),
            (M8_APPENDIX_CSS, ".m8-appendix-page"),
        ):
            print_rules = read_text(path).split("@media print", maxsplit=1)[1]
            self.assertIn(selector, print_rules)
            self.assertIn("display: block;", print_rules)
            self.assertIn("flex: none;", print_rules)

    def test_late_report_pages_use_single_page_background(self) -> None:
        m7_print_rules = read_text(M7_CSS).split("@media print", maxsplit=1)[1]
        m8_css = read_text(M8_APPENDIX_CSS)
        self.assertIn("background: var(--color-bg);", m7_print_rules)
        self.assertNotIn("background: var(--pm-bg-card, #ffffff);", m7_print_rules)
        self.assertIn("background: var(--appendix-color-bg);", m8_css)

    def test_m8_appendix_metrics_are_print_dense(self) -> None:
        # T019-A: M8 CSS may contain multiple @media print blocks (supplement section);
        # search the full stylesheet, not just the last block.
        full_css = read_text(M8_APPENDIX_CSS)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", full_css)

    def test_overview_print_root_uses_compact_block_flow(self) -> None:
        print_rules = read_text(MOV_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".mov-page", print_rules)
        self.assertIn("display: block;", print_rules)
        self.assertIn("flex: none;", print_rules)
        self.assertIn(".mov-page--sparse .mov-card", print_rules)
        self.assertIn("min-height: auto;", print_rules)

    def test_m3_does_not_force_each_domain_panel_to_new_page(self) -> None:
        source = read_text(PDF_UTILS)
        css = read_text(M3_CSS)
        template = read_text(M3_TEMPLATE)
        self.assertNotIn("panel.style.breakBefore = 'page';", source)
        self.assertNotIn("m3-kp-drill__panel--page-break", css)
        self.assertNotIn("m3-kp-drill__panel--page-break", template)

    def test_english_deep_pages_use_compact_print_flow(self) -> None:
        for path, selector in ((M10_CSS, ".m10-page"), (M11_CSS, ".m11-page")):
            print_rules = read_text(path).split("@media print", maxsplit=1)[1]
            self.assertIn(selector, print_rules)
            self.assertIn("display: block;", print_rules)
            self.assertIn("flex: none;", print_rules)

    def test_m11_tail_section_can_stay_with_previous_content(self) -> None:
        print_rules = read_text(M11_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".m11-section:last-child", print_rules)
        self.assertIn("break-inside: auto;", print_rules)
        self.assertIn(".m11-encouragement", print_rules)

    def test_long_tail_modules_have_dense_print_tail_rules(self) -> None:
        m7_print_rules = read_text(M7_CSS).split("@media print", maxsplit=1)[1]
        # m5 tail-grid removed in CSS refactor; verify m7 quality-box compact rules still exist
        self.assertIn(".m7-quality-box", m7_print_rules)
        self.assertIn("display: grid;", m7_print_rules)
        self.assertIn("grid-template-columns: 2fr 1fr;", m7_print_rules)

    def test_m7_dense_print_tail_is_extra_compact(self) -> None:
        print_rules = read_text(M7_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".m7-data-reliability--dense .m7-coverage-table th,", print_rules)
        self.assertIn(".m7-data-reliability--dense .m7-coverage-table td", print_rules)
        self.assertIn("padding: 2px 4px;", print_rules)
        self.assertIn(".m7-data-reliability--dense .m7-quality-block--yellow", print_rules)
        self.assertIn(".m7-data-reliability--dense .m7-quality-block--purple", print_rules)
        self.assertIn(".m7-data-reliability--dense .m7-badge-list", print_rules)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", print_rules)

    def test_m5_long_print_overview_and_tail_are_extra_compact(self) -> None:
        print_rules = read_text(M5_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".m5-city-compare--long .m5-city-compare__overlap-stats", print_rules)
        self.assertIn(".m5-city-compare--long .m5-city-compare__progress-track", print_rules)
        self.assertIn("height: 4px;", print_rules)
        self.assertIn(".m5-city-compare--long .m5-city-compare__table th,", print_rules)
        self.assertIn(".m5-city-compare--long .m5-city-compare__table td", print_rules)
        self.assertIn("padding: 1px 3px;", print_rules)
        # tail-grid removed in CSS refactor; verify footnote compact rules instead
        self.assertIn(".m5-city-compare--long .m5-city-compare__footnote-title", print_rules)

    def test_m9_question_detail_uses_compact_print_flow(self) -> None:
        print_rules = read_text(M9_CSS).split("@media print", maxsplit=1)[1]
        self.assertIn(".m9-page", print_rules)
        self.assertIn("display: block;", print_rules)
        self.assertIn("flex: none;", print_rules)
        self.assertIn(".m9-table th,", print_rules)
        self.assertIn("padding: 3px 5px;", print_rules)


if __name__ == "__main__":
    unittest.main()
