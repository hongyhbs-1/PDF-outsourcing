#!/usr/bin/env python3
"""报告版式密度回归测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from renderer import render_html


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples" / "json"


def render_sample(name: str) -> str:
    payload = json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return render_html(payload)


def extract_student_profile_html(html: str) -> str:
    start = html.index('class="sp-page')
    end = html.index('class="mov-page') if 'class="mov-page' in html else len(html)
    return html[start:end]


class ReportDensityLayoutTest(unittest.TestCase):
    def test_minimal_sample_uses_sparse_density_variants(self) -> None:
        html = render_sample("sample_02_minimal")
        self.assertIn('class="sp-page sp-page--sparse"', html)
        self.assertIn('class="mov-page mov-page--sparse"', html)
        self.assertIn('class="m7-data-reliability m7-data-reliability--sparse"', html)
        self.assertIn('class="m8-appendix-page m8-appendix-page--sparse"', html)

    def test_english_long_sample_uses_dense_density_variants(self) -> None:
        html = render_sample("sample_04_english_rpt2_dual")
        self.assertIn('class="sp-page sp-page--dense"', html)
        self.assertIn('class="m1-report-page m1-report-page--dense"', html)
        self.assertIn('class="m7-data-reliability m7-data-reliability--dense"', html)
        self.assertIn('class="m8-appendix-page m8-appendix-page--dense"', html)

    def test_english_four_paper_city_compare_uses_long_variant(self) -> None:
        html = render_sample("sample_07_english_4paper_long")
        self.assertIn('class="m5-city-compare m5-city-compare--long"', html)

    def test_sample_01_uses_preview_aligned_summary_components(self) -> None:
        html = render_sample("sample_01_math_25q")
        # V5重构后：学生画像用sp-hero-unified替代sp-hero sp-overview-top
        self.assertIn('class="sp-hero-unified"', html)
        self.assertIn("三、核心短板清单", html)
        self.assertIn('class="sp-metric-grid"', html)
        self.assertNotIn(">up<", html)
        self.assertIn('class="mov-hero"', html)
        self.assertIn("12 份样本", html)
        self.assertIn("几何", html)
        self.assertIn("代数", html)
        self.assertIn("DIDA985-20250117-3A7F", html)
        self.assertIn('class="m5-city-compare__progress-fill"', html)
        self.assertIn('class="m5-city-compare__overlap-stats"', html)
        # m9-title only in CSS selectors, not HTML body when m9 not rendered

    def test_sample_01_page4_uses_two_section_information_architecture(self) -> None:
        html = render_sample("sample_01_math_25q")
        page4 = extract_student_profile_html(html)

        # V5重构后：学生画像只有analysis section，overview合并进hero-unified
        self.assertIn('class="sp-section sp-section--analysis"', page4)
        self.assertNotIn('class="sp-section sp-section--overview"', page4)
        self.assertNotIn('class="sp-section sp-section--actions"', page4)
        self.assertNotIn('三、本阶段介入重点', page4)

        # hero-unified应在analysis section之前
        self.assertLess(
            page4.index('class="sp-hero-unified"'),
            page4.index('class="sp-section sp-section--analysis"'),
        )

        # sp-profile-card和sp-hero-main仅在CSS选择器中引用，HTML body不使用
        self.assertIn(".sp-profile-card", html)
        self.assertIn(".sp-hero-main", html)

        self.assertLess(page4.index('class="sp-progress-panel"'), page4.index('class="sp-metric-grid"'))

        metric_order = [
            page4.index('>当前水平<'),
            page4.index('>当前状态<'),
            page4.index('>目标差距<'),
            page4.index('>突破口<'),
        ]
        self.assertEqual(metric_order, sorted(metric_order))


if __name__ == "__main__":
    unittest.main()
