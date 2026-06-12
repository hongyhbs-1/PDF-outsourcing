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
COVER_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m0_cover.jinja2"
STUDENT_PROFILE_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "student_profile.jinja2"
IMPROVEMENT_PREVIEW_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "improvement_preview.jinja2"
REPORT_MASTER_TEMPLATE = PROJECT_ROOT / "templates" / "report_master.jinja2"
MTOC_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m_toc.jinja2"
ENGLISH_TEACHER_NOTE_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m_english_teacher_note.jinja2"
ENGLISH_TEACHER_NOTE_CSS = PROJECT_ROOT / "templates" / "css" / "m_english_teacher_note.css"
ENGLISH_THEME_CSS = PROJECT_ROOT / "templates" / "css" / "english_subject_theme.css"
WORD_REFERENCE_CSS = PROJECT_ROOT / "templates" / "css" / "word_reference_typography.css"
VISUAL_HIERARCHY_CSS = PROJECT_ROOT / "templates" / "css" / "visual_hierarchy.css"
SHARED_CHAPTER_UNDERLINES_CSS = PROJECT_ROOT / "templates" / "css" / "shared_chapter_underlines.css"
M1_CSS = PROJECT_ROOT / "templates" / "css" / "m1_summary.css"
M1_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m1_summary.jinja2"
M2_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m2_core_weakness.jinja2"
M2_CSS = PROJECT_ROOT / "templates" / "css" / "m2_core_weakness.css"
M4_CSS = PROJECT_ROOT / "templates" / "css" / "m4_domains.css"
M5_CSS = PROJECT_ROOT / "templates" / "css" / "m5_city_compare.css"
M6_CSS = PROJECT_ROOT / "templates" / "css" / "m6_tiered_learning.css"
M7_CSS = PROJECT_ROOT / "templates" / "css" / "m7_data_reliability.css"
M8_APPENDIX_CSS = PROJECT_ROOT / "templates" / "css" / "m8_appendix.css"
MOV_CSS = PROJECT_ROOT / "templates" / "css" / "m_overview.css"
M3_CSS = PROJECT_ROOT / "templates" / "css" / "m3_kp_drill.css"
M3_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m3_kp_drill.jinja2"
MOV_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m_overview.jinja2"
M4_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m4_domains.jinja2"
M5_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m5_city_compare.jinja2"
M6_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m6_tiered_learning.jinja2"
M7_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m7_data_reliability.jinja2"
M8_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m8_appendix.jinja2"
M10_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m10_composition.jinja2"
M11_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m11_reading_deep.jinja2"
TEACHER_SUPPLEMENT_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m_teacher_supplement.jinja2"
M10_CSS = PROJECT_ROOT / "templates" / "css" / "m10_composition.css"
M11_CSS = PROJECT_ROOT / "templates" / "css" / "m11_reading_deep.css"
M9_CSS = PROJECT_ROOT / "templates" / "css" / "m9_question_detail.css"
M9_TEMPLATE = PROJECT_ROOT / "templates" / "pages" / "m9_question_detail.jinja2"


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

    def test_cover_uses_print_height_and_sans_font_for_word_reference_parent_p1(self) -> None:
        css = read_text(COVER_CSS)
        cover_named_page = css[css.index("@page cover-page {"):css.index(".m0-cover-page {", css.index("@page cover-page {"))]
        self.assertIn("margin-top: 12mm;", cover_named_page)
        self.assertIn("margin-bottom: 10mm;", cover_named_page)
        self.assertIn("background: var(--pm-bg-page);", cover_named_page)
        self.assertIn("--cover-mt-brand: 20mm;", css)
        self.assertIn("--cover-gap-brand-student: 21.8mm;", css)
        self.assertIn("--cover-gap-student-meta: 8.65mm;", css)
        self.assertIn("--cover-gap-meta-divider: 30mm;", css)
        self.assertIn("--cover-gap-divider-title: 8.75mm;", css)
        self.assertIn("--cover-gap-title-badge: 9mm;", css)
        self.assertIn("--fs-student-name: 17.8mm;", css)
        self.assertIn("--fs-title: 6.22mm;", css)
        self.assertIn("--fs-cover-badge: 4.44mm;", css)
        self.assertIn("--cover-print-fill-height: 305.5mm;", css)
        cover_page = css[css.index(".m0-cover-page {"):css.index("/* Premium: 装饰圆元素", css.index(".m0-cover-page {"))]
        self.assertIn("min-height: var(--cover-print-fill-height);", cover_page)
        self.assertIn('font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;', cover_page)
        cover_content = css[css.index(".m0-cover-content {"):css.index("/* ==========================================================================" , css.index(".m0-cover-content {"))]
        self.assertIn("min-height: var(--cover-print-fill-height);", cover_content)
        meta_block = css[css.index(".m0-cover-meta {"):css.index(".m0-cover-meta__value--empty", css.index(".m0-cover-meta {"))]
        self.assertIn("gap: 5.1mm;", meta_block)
        self.assertIn("transform: translateX(-2.1mm);", meta_block)
        self.assertIn("grid-template-columns: 20.3mm minmax(0, 1fr);", meta_block)
        self.assertIn("column-gap: 11.3mm;", meta_block)
        self.assertIn("font-size: 4.78mm;", meta_block)
        self.assertIn("font-size: 6.89mm;", meta_block)
        compliance = css[css.index(".m0-cover-compliance {"):css.index(".m0-cover-compliance__disclaimer", css.index(".m0-cover-compliance {"))]
        self.assertIn("padding-bottom: 8mm;", compliance)
        self.assertIn("transform: translateY(-0.7mm);", compliance)
        self.assertIn("font-size: 3.22mm;", compliance)
        self.assertIn("font-size: 2.64mm;", compliance)
        print_cover_page = css[css.index("@media print {"):css.index("  .m0-cover-page", css.index("@media print {"))]
        self.assertIn(".module-page--cover", print_cover_page)
        self.assertIn("page: cover-page;", print_cover_page)
        self.assertNotIn("background: #ffffff;", print_cover_page)
        self.assertNotIn("min-height: 330mm;", css)

    def test_cover_ai_review_disclaimer_matches_word_reference_parent_p1(self) -> None:
        template = read_text(COVER_TEMPLATE)
        self.assertIn("人工智能生成，老师审查", template)
        self.assertNotIn("本报告由AI人工智能生成，请结合实际情况使用", template)

    def test_word_reference_cover_title_matches_reference_template(self) -> None:
        template = read_text(COVER_TEMPLATE)
        self.assertIn('word_reference_title = "学情透视分析报告"', template)
        self.assertIn("typography_theme == 'word_reference'", template)
        self.assertIn("{{- _cover_title -}}", template)

    def test_body_page_titles_reuse_shared_report_page_title_style(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        hierarchy_css = read_text(VISUAL_HIERARCHY_CSS)
        underline_css = read_text(SHARED_CHAPTER_UNDERLINES_CSS)
        self.assertIn("--wr-page-title-font-size: 24.5px;", css)
        self.assertIn("--vh-h0-font-size: var(--wr-page-title-font-size);", css)
        self.assertIn("body.word-reference-typography .report-page-title.report-page-title", css)
        self.assertIn("font-size: var(--wr-page-title-font-size) !important;", css)
        self.assertIn("font-weight: var(--wr-page-title-font-weight) !important;", css)
        self.assertIn("line-height: var(--wr-page-title-line-height) !important;", css)
        self.assertIn(".report-page-title,", hierarchy_css)
        self.assertIn(".report-page-title::after", underline_css)
        for selector in (
            ".sp-title",
            ".ip-title",
            ".mov-title",
            ".m1-section-title__text",
            ".m2-cw-module-title",
            ".m3-kp-drill__title",
            ".m4-section-title",
            ".m5-city-compare__title",
            ".m6-module-title__text",
            ".m7-data-reliability__title",
            ".m8-appendix-title__text",
            ".m9-title",
            ".m10-title",
            ".m11-title",
            ".mts-title",
            ".m-english-teacher-note__title",
        ):
            self.assertIn(selector, hierarchy_css)
        expected_title_hooks = {
            STUDENT_PROFILE_TEMPLATE: 'class="report-page-title sp-title"',
            IMPROVEMENT_PREVIEW_TEMPLATE: 'class="report-page-title ip-title"',
            MOV_TEMPLATE: 'class="report-page-title mov-title"',
            M1_TEMPLATE: 'class="report-page-title m1-section-title__text"',
            M2_TEMPLATE: 'class="report-page-title m2-cw-module-title"',
            M3_TEMPLATE: 'class="report-page-title m3-kp-drill__title"',
            M4_TEMPLATE: 'class="report-page-title m4-section-title"',
            M5_TEMPLATE: 'class="report-page-title m5-city-compare__title"',
            M6_TEMPLATE: 'class="report-page-title m6-module-title__text"',
            M7_TEMPLATE: 'class="report-page-title m7-data-reliability__title"',
            M8_TEMPLATE: 'class="report-page-title m8-appendix-title__text"',
            M9_TEMPLATE: 'class="report-page-title m9-title"',
            M10_TEMPLATE: 'class="report-page-title m10-title"',
            M11_TEMPLATE: 'class="report-page-title m11-title"',
            TEACHER_SUPPLEMENT_TEMPLATE: 'class="report-page-title mts-title"',
            ENGLISH_TEACHER_NOTE_TEMPLATE: 'class="report-page-title m-english-teacher-note__title"',
        }
        for template_path, marker in expected_title_hooks.items():
            self.assertIn(marker, read_text(template_path))
        self.assertNotIn("report-page-title", read_text(COVER_TEMPLATE))
        self.assertNotIn("report-page-title", read_text(MTOC_TEMPLATE))
        self.assertNotIn("font-size: 22.5px !important;", css)

    def test_m7_title_compensates_golden_typeset_wrapper_zoom(self) -> None:
        from golden_typeset.css_builder import build_css
        from golden_typeset.math_func import Block, PageLayout

        compressed_layout = PageLayout(
            blocks=[Block("title", 10.0), Block("core", 20.0), Block("content", 500.0)],
            content_h=530.0,
            gaps_h=0.0,
            top_pad=0.0,
            bottom_pad=0.0,
            scale=0.5,
            unit_u=0.0,
            content_ratio=1.0,
        )
        css = build_css({"m7": compressed_layout})
        self.assertIn("#toc-m7 > .m7-data-reliability {", css)
        self.assertIn("zoom: 0.5000;", css)
        self.assertIn("#toc-m7 > .m7-data-reliability > .report-page-title", css)
        self.assertIn("keep shared page-title typography visually consistent under wrapper zoom", css)
        self.assertIn("zoom: 2.0000;", css)

    def test_word_reference_student_profile_p2_matches_reference_scale(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        self.assertIn("Parent P2 student-profile pages", css)
        self.assertIn("body.word-reference-typography .sp-page > .module-content-card", css)
        self.assertIn("min-height: 224mm !important;", css)
        self.assertIn("padding: 20px 21px 20px 23px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .sp-page > .module-content-card", css)
        self.assertIn("min-height: 206mm !important;", css)
        self.assertIn("font-size: var(--wr-page-title-font-size) !important;", css)
        self.assertIn("body.word-reference-typography .sp-page > .report-page-title.report-page-title", css)
        self.assertIn("zoom: 0.9709 !important;", css)
        self.assertIn("body.word-reference-typography .sp-hero-unified__title", css)
        self.assertIn("font-size: 21.2px !important;", css)
        self.assertIn("body.word-reference-typography .sp-page .sp-hero-unified + .sp-section-divider", css)
        self.assertIn("margin: 32px 0 25px !important;", css)
        self.assertIn("body.word-reference-typography .sp-progress-panel__title", css)
        self.assertIn("font-size: 16.6px !important;", css)
        self.assertIn('--word-ref-font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;', css)
        self.assertIn("body.word-reference-typography:not(.report-theme--english) .sp-metric-card", css)
        self.assertIn("min-height: 136px !important;", css)
        self.assertIn("body.word-reference-typography:not(.report-theme--english) .sp-analysis-card--weakness", css)
        self.assertIn("min-height: 314px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .sp-analysis-card--weakness", css)
        self.assertIn("min-height: 248px !important;", css)
        self.assertIn("body.word-reference-typography .sp-metric-card__value", css)
        self.assertIn("font-size: 20px !important;", css)
        self.assertIn("body.word-reference-typography .sp-metric-card__value--current", css)
        self.assertIn("color: var(--pm-teal) !important;", css)
        self.assertIn("body.word-reference-typography .sp-metric-card__value--pos", css)
        self.assertIn("color: var(--pm-status-success, var(--cc-success-green)) !important;", css)
        template = read_text(STUDENT_PROFILE_TEMPLATE)
        self.assertIn("先看位置，再看后面的分析重点。", template)
        self.assertNotIn("目标线仅作达标参考，后续重点看高分稳定性与薄弱领域。", template)

    def test_word_reference_improvement_preview_p3_matches_reference_scale(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        self.assertIn("Parent P3 improvement-preview pages", css)
        self.assertIn("body.word-reference-typography .ip-page > .module-content-card", css)
        self.assertIn("min-height: 216mm !important;", css)
        self.assertIn("body.word-reference-typography .ip-title", css)
        self.assertIn("margin: 10px 0 16px 3px !important;", css)
        self.assertIn("body.word-reference-typography .ip-intervention-bar", css)
        self.assertIn("padding: 6px 10px !important;", css)
        self.assertIn("body.word-reference-typography .ip-roadmap", css)
        self.assertIn("margin-bottom: 14px !important;", css)
        self.assertIn("body.word-reference-typography .ip-focus-item__gain", css)
        self.assertIn("color: var(--pm-status-success, var(--cc-success-green)) !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .ip-roadmap", css)
        self.assertIn("margin-bottom: 8px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .ip-parent-guide", css)
        self.assertIn("margin-top: 8px !important;", css)
        template = read_text(IMPROVEMENT_PREVIEW_TEMPLATE)
        self.assertIn("{% set focus_items = [] %}", template)
        self.assertIn("{% set focus_limit = 3 if subject == '英语' else 4 %}", template)
        self.assertIn("focus_target_acc = stretch_target_acc if tier == 'excellent' else target_acc", template)
        self.assertIn("主攻 {{ ip_lead }}{% if focus_items | length > 1 %}，跟进 {{ ip_secondary }}{% endif %}，巩固优势领域", template)
        self.assertIn("当前水平", template)
        self.assertIn("快速提升", template)
        self.assertIn("目标达成", template)
        self.assertIn("{% if focus_items | length > 0 %}", template)
        self.assertIn("+{{ '%.1f' | format(focus_gain) }}%", template)

    def test_toc_title_and_item_numbers_match_reference_template(self) -> None:
        template = read_text(MTOC_TEMPLATE)
        self.assertIn('<h1 class="mtoc-title">目录</h1>', template)
        for number in ("1", "2", "3", "4", "5", "6", "7"):
            self.assertIn(f'<span class="mtoc-item__number">{number}</span>', template)
        self.assertIn("{% if _show_question_detail_toc %}8{% else %}7{% endif %}", template)
        self.assertNotIn('<h1 class="mtoc-title">目 录</h1>', template)
        self.assertNotIn('<span class="mtoc-item__number">一</span>', template)

    def test_word_reference_toc_p5_matches_reference_scale(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        self.assertIn("Parent P5 table of contents", css)
        self.assertIn("body.word-reference-typography .mtoc-page", css)
        self.assertIn("zoom: 1.04 !important;", css)
        self.assertIn("min-height: 264mm !important;", css)
        self.assertIn("padding: 2mm 16mm 0 20mm !important;", css)
        self.assertIn("body.word-reference-typography .mtoc-title", css)
        self.assertIn("font-size: 28.9px !important;", css)
        self.assertIn("letter-spacing: 0.5em !important;", css)
        self.assertIn("body.word-reference-typography .mtoc-item__number", css)
        self.assertIn("font-size: 22.2px !important;", css)
        self.assertIn("body.word-reference-typography .mtoc-item__page", css)
        self.assertIn("font-size: 20px !important;", css)
        self.assertIn("body.word-reference-typography .mtoc-reading-guide__item", css)
        self.assertIn("font-size: 14.4px !important;", css)
        template = read_text(MTOC_TEMPLATE)
        self.assertIn("先看<strong>诊断摘要</strong>了解整体水平，再看<strong>领域达标分析</strong>定位薄弱方向。", template)
        self.assertIn("重点关注<strong>核心短板清单</strong>中的高优先级项目，把它们转成下一阶段训练任务。", template)
        self.assertIn("对照<strong>逐题分析明细</strong>回看错题，确认薄弱环节的具体表现。", template)
        self.assertNotIn("六大领域达标分析</strong>定位薄弱方向", template)
        self.assertNotIn("P0 级知识点，这些是提分最快的突破口", template)
        self.assertNotIn("逐题回顾错题，理解薄弱环节", template)

    def test_word_reference_m1_p6_matches_reference_scale(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        self.assertIn("Parent P6 diagnostic-summary page", css)
        self.assertIn("body.word-reference-typography .m1-report-page", css)
        self.assertIn("padding: 0 16mm 0 20.5mm !important;", css)
        self.assertIn("body.word-reference-typography .m1-section-title__text", css)
        self.assertIn("font-size: var(--wr-page-title-font-size) !important;", css)
        self.assertIn("body.word-reference-typography .m1-core-conclusion__text", css)
        self.assertIn("font-size: 14.4px !important;", css)
        self.assertIn("body.word-reference-typography .m1-section-bar", css)
        self.assertIn("font-size: 13.9px !important;", css)
        self.assertIn("body.word-reference-typography .m1-donut-center", css)
        self.assertIn("font-size: 35.6px !important;", css)
        self.assertIn("body.word-reference-typography .m1-chart-note", css)
        self.assertIn("font-size: 14.7px !important;", css)
        self.assertIn("margin: 17px 0 20px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .m1-chart-note", css)
        self.assertIn("margin: 29px 0 28px !important;", css)
        self.assertIn("body.word-reference-typography .m1-finding-item", css)
        self.assertIn("font-size: 15.5px !important;", css)
        self.assertIn("body.word-reference-typography:not(.report-theme--english) .m1-findings-inline", css)
        self.assertIn("min-height: 160px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .m1-findings-inline", css)
        self.assertIn("min-height: 120px !important;", css)
        self.assertIn("body.word-reference-typography .m1-bt-title", css)
        self.assertIn("font-size: 13.3px !important;", css)
        self.assertIn("body.word-reference-typography .m1-suggestion-callout", css)
        self.assertIn("font-size: 14.7px !important;", css)

    def test_english_parent_deep_pages_are_visibility_controlled_with_teacher_note(self) -> None:
        master = read_text(REPORT_MASTER_TEMPLATE)
        self.assertIn("_show_m10_composition = pv.m10_composition | default(false)", master)
        self.assertIn("_show_m11_reading_deep = pv.m11_reading_deep | default(false)", master)
        self.assertIn("_show_english_teacher_note", master)
        self.assertIn("pages/m_english_teacher_note.jinja2", master)
        note = read_text(ENGLISH_TEACHER_NOTE_TEMPLATE)
        self.assertIn("教师解读", note)
        self.assertIn("作文和阅读部分分析请联系老师精讲", note)
        note_css = read_text(ENGLISH_TEACHER_NOTE_CSS)
        self.assertIn(".m-english-teacher-note__title", note_css)
        self.assertNotIn("style=", note)

    def test_m9_continuation_pages_do_not_emit_extra_titles(self) -> None:
        template = read_text(M9_TEMPLATE)
        self.assertNotIn("逐题分析明细（续）", template)
        self.assertNotIn("m9-continuation-header__meta", template)
        self.assertIn("与参考模板一致, 直接延续表格内容", template)

    def test_english_overview_card_can_stay_with_title_on_p4(self) -> None:
        css = read_text(WORD_REFERENCE_CSS)
        self.assertIn("Parent P4 overview page", css)
        self.assertIn("body.word-reference-typography .mov-page", css)
        self.assertIn("zoom: 1 !important;", css)
        self.assertIn("body.word-reference-typography .mov-page > .module-content-card", css)
        self.assertIn("break-inside: auto !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .mov-title-section", css)
        self.assertIn("margin-bottom: -8px !important;", css)
        self.assertIn("body.word-reference-typography.report-theme--english .mov-page > .module-content-card", css)
        self.assertIn("min-height: 153mm !important;", css)
        self.assertIn("body.word-reference-typography:not(.report-theme--english) .mov-page > .module-content-card", css)
        self.assertIn("min-height: 188mm !important;", css)
        self.assertIn("body.word-reference-typography .mov-pie__slice", css)
        self.assertIn("print-color-adjust: exact !important;", css)
        self.assertIn("without splitting to P5", css)
        self.assertNotIn("zoom: 0.82 !important;", css)

    def test_word_reference_cover_page_keeps_beige_paper_band_on_p1(self) -> None:
        source = read_text(PDF_UTILS)
        self.assertNotIn("cover_footer_overlay", source)
        self.assertNotIn("draw_cover_footer_overlay", source)
        css = read_text(COVER_CSS)
        cover_named_page = css[css.index("@page cover-page {"):css.index(".m0-cover-page {", css.index("@page cover-page {"))]
        self.assertIn("background: var(--pm-bg-page);", cover_named_page)

    def test_english_theme_keeps_cover_paper_beige_and_body_pages_blue(self) -> None:
        css = read_text(ENGLISH_THEME_CSS)
        body_page_setup = css[css.index("body.report-theme--english {"):css.index("body.report-theme--english .module-page,", css.index("body.report-theme--english {"))]
        self.assertIn("background: var(--cc-english-page-bg);", body_page_setup)
        self.assertIn("background: var(--cc-english-page-bg);", body_page_setup.split("@page english-report", maxsplit=1)[1])
        report_cover = css[css.index("@page report-cover {"):css.index("body.report-theme--english .module-page.module-page--cover::before", css.index("@page report-cover {"))]
        self.assertIn("background: var(--cc-page-bg);", report_cover)
        self.assertIn("page: report-cover;", report_cover)
        cover_page = css[css.index("body.report-theme--english .m0-cover-page {"):css.index("body.report-theme--english .m0-cover-page::after", css.index("body.report-theme--english .m0-cover-page {"))]
        self.assertIn("linear-gradient(180deg, #f8f5ef 0%, #ffffff 40%);", cover_page)
        self.assertNotIn("linear-gradient(180deg, var(--cc-page-bg) 0%, var(--cc-card-bg) 40%);", cover_page)

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
