"""English brief-report-rem adapter.

Migrated from render_standalone.py — pure move refactor.
Adapts production brief-report-rem JSON payloads to the unified
report_master data contract.
"""

from __future__ import annotations


class EnglishBriefAdapter:
    """Adapter for brief-report-rem payload schema (English samples)."""

    # -- public protocol --------------------------------------------------

    @staticmethod
    def detect(payload: dict) -> bool:
        """Return True for brief-report-rem payloads from production samples."""
        if not isinstance(payload, dict):
            return False
        meta = payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {}
        sections = (
            payload.get("sections", {})
            if isinstance(payload.get("sections"), dict)
            else {}
        )
        return (
            payload.get("schema_version") == "render_payload.v1"
            and meta.get("render_template") == "brief-report-rem"
            and "section_1_high_freq" in sections
        )

    def adapt(self, payload: dict) -> dict:
        """Adapt brief-report-rem sample to the full report_master data contract."""
        sections = payload.get("sections") or {}
        meta = _build_meta(payload)
        domains = dict(sections.get("section_2_domains") or {})
        summary = _build_summary(sections)
        core_weakness = _build_core_weakness(sections)
        target_accuracy = summary.get("target_accuracy")
        domains.setdefault("target_accuracy", target_accuracy)

        normalized = dict(payload)
        normalized.update(
            {
                "meta": meta,
                "cover": _build_cover(payload, meta),
                "summary": summary,
                "domains": domains,
                "section_2_domains": domains,
                "core_weakness": core_weakness,
                "section_core_weakness": core_weakness,
                "kp_drill": _build_kp_drill(),
                "data_reliability": {
                    "section_4_coverage": sections.get("section_4_coverage") or {}
                },
                "appendix": _build_appendix(sections, meta),
                "key_findings": [],
                "breakthrough": sections.get("section_3_breakthrough") or {},
                "suggestion": {
                    "text": (sections.get("section_3_breakthrough") or {}).get(
                        "note_text", ""
                    )
                },
                "city_compare": {
                    "has_data": False,
                    "overlap_items": [],
                    "overlap_summary": {"has_data": False},
                },
                "tiered_learning": _build_tiered_learning(summary, domains, meta),
                "page_visibility": {
                    "m5_city_compare": False,
                    "m10_composition": False,
                    "m11_reading_deep": False,
                    "show_teacher_supplement": False,
                },
            }
        )
        return normalized


# -- internal helpers (logic unchanged from render_standalone.py) ------


def _build_meta(payload: dict) -> dict:
    meta = dict(payload.get("meta") or {})
    title = payload.get("title") or payload.get("header_title") or "基线定位分析报告"
    meta.setdefault("subject", "english")
    meta.setdefault("subject_name", "英语")
    meta.setdefault("report_title", title)
    meta.setdefault("report_name", title)
    meta.setdefault("left_title", title)
    meta.setdefault("page_title", title)
    meta.setdefault("module_title", title)
    return meta


def _build_cover(payload: dict, meta: dict) -> dict:
    return {
        "badge_text": "学情诊断",
        "brand": {"name": "dida985", "logo_url": ""},
        "title": payload.get("title") or meta.get("report_title") or "基线定位分析报告",
        "subject": meta.get("subject_name", "英语"),
        "cover_meta": {
            "student_name": meta.get("student_display_name", ""),
            "city_name": meta.get("city_name", ""),
            "grade": meta.get("grade", ""),
            "report_date": meta.get("report_date", ""),
            "subject": meta.get("subject_name", "英语"),
        },
        "footer_tagline": "逐题透析 · 逐点拆解 · 对标历年真题考点",
    }


def _build_summary(sections: dict) -> dict:
    high_freq = sections.get("section_1_high_freq") or {}
    target = high_freq.get("target") or {}
    chart = high_freq.get("chart") or {}
    segments = chart.get("segments") or []
    pass_rate = chart.get("pass_rate", 0)
    target_accuracy = target.get("target_accuracy", 85)
    return {
        "banner_text": high_freq.get("note_text", "基于高频考点分析生成诊断摘要。"),
        "target_score_text": target.get("target_score_text", "--"),
        "target_accuracy": target_accuracy,
        "target_accuracy_text": target.get("target_accuracy_text", "--"),
        "current_accuracy": pass_rate,
        "current_accuracy_text": chart.get("pass_rate_text", "--"),
        "current_delta": round(float(pass_rate or 0) - float(target_accuracy or 0), 1),
        "current_delta_text": f"{round(float(pass_rate or 0) - float(target_accuracy or 0), 1):+g}%",
        "current_trend": "stable",
        "pass_rate": pass_rate,
        "pass_rate_text": chart.get("pass_rate_text", "--"),
        "pass_segments": segments,
        "high_freq_kp_total": high_freq.get("high_freq_kp_total", 0),
        "high_freq_kp_total_text": high_freq.get("high_freq_kp_total_text", ""),
    }


def _build_core_weakness(sections: dict) -> dict:
    breakthrough = sections.get("section_3_breakthrough") or {}
    items = breakthrough.get("items") or []
    has_data = bool(items) and not breakthrough.get("all_achieved", False)
    return {
        "module_title": breakthrough.get("title") or "个性化突破路径",
        "intro_text": breakthrough.get("note_text")
        or "建议结合高频考点结果安排专项练习。",
        "legend": [],
        "table_columns": [],
        "items": items,
        "has_data": has_data,
        "empty_guidance": breakthrough.get("note_text")
        or "当前没有需要优先展示的核心短板。",
        "reasoning": {"summary_text": breakthrough.get("note_text", "")},
        "tips": [breakthrough.get("cta_text", "")],
    }


def _build_kp_drill() -> dict:
    return {
        "module_title": "知识点短板钻取",
        "intro_text": "该精简报告样本未携带逐知识点钻取明细。",
        "has_data": False,
        "level_guide": [],
        "tables": {},
        "path_example": {},
        "domain_panels": [],
        "header": {},
    }


def _build_tiered_learning(summary: dict, domains: dict, meta: dict) -> dict:
    current_accuracy = summary.get("current_accuracy", 0)
    target_accuracy = summary.get("target_accuracy", 85)
    above_target = float(current_accuracy or 0) >= float(target_accuracy or 0)
    return {
        "page_header": {
            "report_name": meta.get("report_name", "基线定位分析报告"),
            "report_date": meta.get("report_date", "--"),
        },
        "module": {
            "title": "分层与学习建议",
            "cards": {
                "stage_judgement": {
                    "title": "当前学习阶段判定",
                    "target_accuracy": target_accuracy,
                    "current": {
                        "has_data": True,
                        "pass_rate": current_accuracy,
                        "target_accuracy": target_accuracy,
                        "above_target": above_target,
                        "stage_key": "excellent" if above_target else "room_grow",
                    },
                    "stages": [
                        {"key": "need_major", "name": "基础巩固期"},
                        {"key": "room_grow", "name": "专项突破期"},
                        {"key": "excellent", "name": "稳定提升期"},
                    ],
                },
                "student_suggestion": {
                    "summary": "按当前薄弱领域安排短周期专项练习。",
                    "sections": [],
                },
                "parent_guidance": {
                    "summary": "关注训练节奏，优先支持补测、专项和回测闭环。",
                    "checklist": [],
                },
                "teacher_guidance": {
                    "summary": domains.get(
                        "note_text", "建议结合达标总览制定教学安排。"
                    ),
                    "checklist": [],
                },
            },
        },
    }


def _build_appendix(sections: dict, meta: dict) -> dict:
    coverage = sections.get("section_4_coverage") or {}
    stats = coverage.get("stats") or {}
    return {
        "analysis_scope": {
            "title": coverage.get("title", "题检覆盖情况说明"),
            "items": [
                {"label": "题量", "value": stats.get("total_questions_text", "--")},
                {"label": "L2覆盖", "value": stats.get("l2_covered_text", "--")},
                {"label": "分析周期", "value": stats.get("test_period", "--")},
            ],
        },
        "difficulty": {},
        "papers": [],
        "metric_definitions": [
            {
                "name": "目标正确率",
                "description": "达到目标分数对应的知识点正确率参考线。",
            },
            {"name": "达标率", "description": "达到目标正确率的高频考点占比。"},
        ],
    }
