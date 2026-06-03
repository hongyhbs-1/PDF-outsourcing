#!/usr/bin/env python3
"""审计样本 JSON 与渲染 HTML 的关键数据一致性。"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from renderer import render_html


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples" / "json"
STATUS_OK = "ok"
STATUS_MISMATCH = "mismatch"
STATUS_SOURCE_MISSING = "source_missing"
STATUS_RENDERED_MISSING = "rendered_missing"


@dataclass(frozen=True)
class AuditResult:
    sample: str
    module: str
    metric: str
    source_path: str
    source_value: str
    rendered_value: str
    status: str


def body_without_css(rendered_html: str) -> str:
    if "</style>" not in rendered_html:
        return rendered_html
    return rendered_html.split("</style>", maxsplit=1)[1]


def visible_text(rendered_html: str) -> str:
    body = body_without_css(rendered_html)
    text = re.sub(r"<[^>]+>", " ", body)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def make_result(
    sample: str,
    module: str,
    metric: str,
    source_path: str,
    source_value: object,
    rendered_value: object,
    status: str,
) -> AuditResult:
    return AuditResult(
        sample=sample,
        module=module,
        metric=metric,
        source_path=source_path,
        source_value=str(source_value),
        rendered_value=str(rendered_value),
        status=status,
    )


def text_metric(
    sample: str,
    module: str,
    metric: str,
    source_path: str,
    source_value: object,
    text: str,
) -> AuditResult:
    if source_value is None or source_value == "":
        return make_result(sample, module, metric, source_path, source_value, "", STATUS_SOURCE_MISSING)
    expected = str(source_value)
    status = STATUS_OK if expected in text else STATUS_RENDERED_MISSING
    rendered = expected if status == STATUS_OK else ""
    return make_result(sample, module, metric, source_path, expected, rendered, status)


def status_metric(
    sample: str,
    module: str,
    metric: str,
    source_path: str,
    source_value: object,
    text: str,
) -> AuditResult:
    if source_value in ("无数据", "nodata"):
        rendered = "数据不充分" if "数据不充分" in text else ""
        status = STATUS_OK if rendered else STATUS_RENDERED_MISSING
        return make_result(sample, module, metric, source_path, source_value, rendered, status)
    return text_metric(sample, module, metric, source_path, source_value, text)


def count_metric(
    sample: str,
    module: str,
    metric: str,
    source_path: str,
    source_value: int,
    rendered_value: int,
) -> AuditResult:
    status = STATUS_OK if source_value == rendered_value else STATUS_MISMATCH
    return make_result(sample, module, metric, source_path, source_value, rendered_value, status)


def extract_class_texts(rendered_html: str, class_name: str) -> list[str]:
    pattern = rf'class="{re.escape(class_name)}"[^>]*>\s*([^<]+?)\s*</'
    return [html_lib.unescape(item.strip()) for item in re.findall(pattern, body_without_css(rendered_html))]


def extract_question_detail_overview(rendered_html: str) -> list[str]:
    return extract_class_texts(rendered_html, "m9-overview__stat-num")[:4]


def extract_city_overlap_ratio(rendered_html: str) -> str:
    values = extract_class_texts(rendered_html, "m5-city-compare__overlap-num")
    return values[0] if values else ""


def extract_city_overlap_stat(rendered_html: str, label: str) -> str:
    body = body_without_css(rendered_html)
    pattern = rf"{re.escape(label)}.*?m5-city-compare__overlap-stat-value[^>]*>\s*([^<]+)"
    match = re.search(pattern, body, flags=re.S)
    return html_lib.unescape(match.group(1).strip()) if match else ""


def audit_m1(sample: str, payload: dict, rendered_html: str, text: str) -> list[AuditResult]:
    summary = payload.get("summary", {})
    items = payload.get("breakthrough", {}).get("items", [])
    rendered_count = body_without_css(rendered_html).count('class="m1-breakthrough-card"')
    return [
        text_metric(sample, "M1", "当前正确率", "summary.current_accuracy_text", summary.get("current_accuracy_text"), text),
        text_metric(sample, "M1", "目标正确率", "summary.target_accuracy_text", summary.get("target_accuracy_text"), text),
        text_metric(sample, "M1", "达标率", "summary.pass_rate_text", summary.get("pass_rate_text"), text),
        count_metric(sample, "M1", "P0突破项数量", "breakthrough.items", len(items), rendered_count),
    ]


def audit_m4(sample: str, payload: dict, text: str) -> list[AuditResult]:
    results: list[AuditResult] = []
    domains = payload.get("domains", {}).get("domain_items", [])
    for index, item in enumerate(domains):
        label = f"领域{index + 1}"
        name = item.get("name_cn") or item.get("name")
        accuracy = item.get("accuracy_text")
        status = item.get("status")
        results.append(text_metric(sample, "M4", f"{label}名称", f"domains.domain_items[{index}].name_cn", name, text))
        results.append(text_metric(sample, "M4", f"{label}正确率", f"domains.domain_items[{index}].accuracy_text", accuracy, text))
        results.append(status_metric(sample, "M4", f"{label}状态", f"domains.domain_items[{index}].status", status, text))
    return results


def audit_m5(sample: str, payload: dict, rendered_html: str, text: str) -> list[AuditResult]:
    summary = payload.get("city_compare", {}).get("overlap_summary", {})
    items = payload.get("city_compare", {}).get("overlap_items", [])
    ratio = summary.get("overlap_ratio")
    ratio_text = f"{int(round(ratio if ratio > 1 else ratio * 100))}%" if ratio is not None else None
    rendered_count = extract_city_overlap_stat(rendered_html, "重合知识点")
    rendered_ratio = extract_city_overlap_ratio(rendered_html)
    return [
        text_metric(sample, "M5", "核心短板总数", "city_compare.overlap_summary.student_core_weak_total", summary.get("student_core_weak_total"), text),
        text_metric(sample, "M5", "城市TopN", "city_compare.overlap_summary.city_top_n", summary.get("city_top_n"), text),
        count_metric(sample, "M5", "高频交集项数量", "city_compare.overlap_items", len(items), len(items)),
        make_result(sample, "M5", "交集数量", "city_compare.overlap_summary.overlap_count", summary.get("overlap_count"), rendered_count, STATUS_OK if str(summary.get("overlap_count")) == rendered_count else STATUS_MISMATCH),
        make_result(sample, "M5", "重合率", "city_compare.overlap_summary.overlap_ratio", ratio_text, rendered_ratio, STATUS_OK if ratio_text == rendered_ratio else STATUS_MISMATCH),
    ]


def audit_m7_m8(sample: str, payload: dict, text: str) -> list[AuditResult]:
    stats = payload.get("data_reliability", {}).get("section_4_coverage", {}).get("stats", {})
    papers = payload.get("appendix", {}).get("papers", {})
    return [
        text_metric(sample, "M7", "分析题量", "data_reliability.section_4_coverage.stats.total_questions", stats.get("total_questions"), text),
        text_metric(sample, "M7", "L3覆盖数", "data_reliability.section_4_coverage.stats.l3_covered", stats.get("l3_covered"), text),
        text_metric(sample, "M7", "L3总数", "data_reliability.section_4_coverage.stats.l3_total", stats.get("l3_total"), text),
        text_metric(sample, "M8", "附录总题数", "appendix.papers.total_questions", papers.get("total_questions"), text),
        text_metric(sample, "M8", "附录试卷数", "appendix.papers.total_papers", papers.get("total_papers"), text),
    ]


def audit_m9(sample: str, payload: dict, rendered_html: str) -> list[AuditResult]:
    qd = payload.get("question_detail")
    if not qd:
        return [make_result(sample, "M9", "逐题数据", "question_detail", "", "", STATUS_SOURCE_MISSING)]
    rendered = extract_question_detail_overview(rendered_html)
    expected = [
        str(qd.get("total_count")),
        str(qd.get("wrong_count")),
        str(qd.get("correct_count", qd.get("total_count", 0) - qd.get("wrong_count", 0))),
        str(len(qd.get("papers", []))),
    ]
    labels = ["总题数", "错题数", "正确数", "试卷数"]
    paths = ["total_count", "wrong_count", "correct_count", "papers"]
    results: list[AuditResult] = []
    for index, label in enumerate(labels):
        value = rendered[index] if index < len(rendered) else ""
        status = STATUS_OK if expected[index] == value else STATUS_MISMATCH
        results.append(make_result(sample, "M9", label, f"question_detail.{paths[index]}", expected[index], value, status))
    return results


def audit_payload(sample: str, payload: dict, rendered_html: str) -> list[AuditResult]:
    text = visible_text(rendered_html)
    results: list[AuditResult] = []
    results.extend(audit_m1(sample, payload, rendered_html, text))
    results.extend(audit_m4(sample, payload, text))
    results.extend(audit_m5(sample, payload, rendered_html, text))
    results.extend(audit_m7_m8(sample, payload, text))
    results.extend(audit_m9(sample, payload, rendered_html))
    return results


def audit_sample_file(path: Path) -> list[AuditResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rendered_html = render_html(payload)
    return audit_payload(path.stem, payload, rendered_html)


def print_results(results: list[AuditResult]) -> None:
    print("sample\tmodule\tmetric\tsource_path\tsource_value\trendered_value\tstatus")
    for item in results:
        print(
            f"{item.sample}\t{item.module}\t{item.metric}\t{item.source_path}\t"
            f"{item.source_value}\t{item.rendered_value}\t{item.status}"
        )


def main() -> int:
    all_results: list[AuditResult] = []
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        all_results.extend(audit_sample_file(path))
    print_results(all_results)
    return 1 if any(item.status == STATUS_MISMATCH for item in all_results) else 0


if __name__ == "__main__":
    sys.exit(main())
