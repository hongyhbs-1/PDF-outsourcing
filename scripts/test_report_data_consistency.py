#!/usr/bin/env python3
"""报告数据一致性回归测试。"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import audit_report_data_consistency as audit
import render_standalone


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples" / "json"


def load_sample(name: str) -> dict:
    path = SAMPLES_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


class ReportDataConsistencyTest(unittest.TestCase):
    def test_sample_04_key_counts_match_rendered_html(self) -> None:
        payload = load_sample("sample_04_english_rpt2_dual")
        html = render_standalone.render_html(payload)

        results = audit.audit_payload("sample_04_english_rpt2_dual", payload, html)
        mismatches = [item for item in results if item.status == "mismatch"]

        self.assertEqual([], mismatches)

    def test_question_detail_counts_are_not_hardcoded(self) -> None:
        payload = copy.deepcopy(load_sample("sample_04_english_rpt2_dual"))
        payload["question_detail"]["total_count"] = 107
        payload["question_detail"]["wrong_count"] = 99
        payload["question_detail"]["correct_count"] = 8

        html = render_standalone.render_html(payload)
        values = audit.extract_question_detail_overview(html)

        self.assertEqual(["107", "99", "8", "2"], values)

    def test_summary_accuracy_uses_payload_value(self) -> None:
        payload = copy.deepcopy(load_sample("sample_04_english_rpt2_dual"))
        payload["summary"]["current_accuracy"] = 12.3
        payload["summary"]["current_accuracy_text"] = "12.3%"
        payload["summary"]["pass_rate"] = 34.5
        payload["summary"]["pass_rate_text"] = "34.5%"

        html = render_standalone.render_html(payload)
        results = audit.audit_payload("mutated", payload, html)
        by_metric = {(item.module, item.metric): item for item in results}

        self.assertEqual("ok", by_metric[("M1", "当前正确率")].status)
        self.assertEqual("ok", by_metric[("M1", "达标率")].status)


if __name__ == "__main__":
    unittest.main()

