"""Build two-page learning blueprint view models from RenderPayload.

This module converts the existing report RenderPayload into two clean
view-models that are easy for Jinja2 templates to render:

    - diagnostic_blueprint: page 1, student diagnostic panorama
    - execution_blueprint: page 2, tutoring execution and tracking panorama

Usage in render_standalone.py:

    from learning_blueprint_builder import build_learning_blueprints
    context.update(build_learning_blueprints(payload))

The builder is intentionally defensive: missing fields degrade to safe labels
instead of breaking the PDF renderer.
"""
from __future__ import annotations

import math
import re
from typing import Any


MATH_DOMAINS = [
    ("equation", "方程与不等式", "≠"),
    ("function", "函数", "ƒ"),
    ("number", "数与代数", "π"),
    ("statistics", "统计与概率", "◔"),
    ("application", "应用问题", "▧"),
    ("geometry", "几何", "△"),
]

DOMAIN_BY_CODE_PREFIX = {
    "1": "方程与不等式",
    "2": "函数",
    "3": "数与代数",
    "4": "统计与概率",
    "5": "应用问题",
    "6": "几何",
}

DOMAIN_POSITIONS = {
    "equation": {"x": 300, "y": 58},
    "function": {"x": 502, "y": 175},
    "number": {"x": 502, "y": 407},
    "statistics": {"x": 300, "y": 525},
    "application": {"x": 98, "y": 407},
    "geometry": {"x": 98, "y": 175},
}

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "补测": 4, "待测": 4, "—": 9, "": 9}


def _get(obj: Any, path: str, default: Any = None) -> Any:
    """Safe dotted-path getter for nested dict/list structures."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except Exception:
                return default
        else:
            return default
    return default if cur is None else cur


def _first(*values: Any, default: Any = "") -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return default


def _num(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return default
    return float(match.group(0))


def _pct_num(value: Any, default: float | None = None) -> float | None:
    n = _num(value, default)
    if n is None:
        return default
    # Some pipelines use 0.72, others use 72. Treat <=1 as a ratio.
    if 0 <= n <= 1:
        return n * 100
    return n


def _fmt_pct(value: Any, default: str = "—") -> str:
    n = _pct_num(value, None)
    if n is None:
        return default
    if abs(n - round(n)) < 0.05:
        return f"{int(round(n))}%"
    return f"{n:.1f}%"


def _fmt_signed_pct(value: Any, default: str = "—") -> str:
    n = _pct_num(value, None)
    if n is None:
        return default
    sign = "+" if n > 0 else ""
    if abs(n - round(n)) < 0.05:
        return f"{sign}{int(round(n))}%"
    return f"{sign}{n:.1f}%"


def _fmt_int(value: Any, default: str = "—") -> str:
    n = _num(value, None)
    if n is None:
        return default
    return str(int(round(n)))


def _fmt_score(value: Any, default: str = "—") -> str:
    n = _num(value, None)
    if n is None:
        return default
    if abs(n - round(n)) < 0.01:
        return f"{n:.0f}"
    return f"{n:.2f}".rstrip("0").rstrip(".")


def _state_from_accuracy(accuracy: Any, target: Any, has_data: bool = True) -> str:
    if not has_data:
        return "nodata"
    acc = _pct_num(accuracy, None)
    tgt = _pct_num(target, 85.0)
    if acc is None:
        return "nodata"
    if acc >= tgt:
        return "achieved"
    if tgt - acc <= 10:
        return "attention"
    return "improve"


def _state_label(state: str) -> str:
    return {
        "achieved": "已达标",
        "attention": "需关注",
        "improve": "待提升",
        "nodata": "题目太少",
        "need_test": "优先补测",
        "weak": "高频+薄弱",
        "ok": "保持巩固",
    }.get(state, "待确认")


def _priority_class(priority: str) -> str:
    return str(priority or "P2").lower().replace("补测", "test")


def _infer_domain_from_code(
    code: Any,
    fallback: str = "待确认",
    domain_by_prefix: dict[str, str] | None = None,
) -> str:
    if not code:
        return fallback
    prefix = str(code).split(".", 1)[0]
    if domain_by_prefix and prefix in domain_by_prefix:
        return domain_by_prefix[prefix]
    return DOMAIN_BY_CODE_PREFIX.get(prefix, fallback)


def _looks_like_code(value: Any) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)*", str(value or "")))


def _domain_name_by_code_prefix(payload: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in _get(payload, "domains.domain_items", []) or []:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        name = _first(item.get("domain_name"), item.get("name_cn"), item.get("name"), default="")
        if code and name:
            mapping[str(code).split(".", 1)[0]] = str(name)
    return mapping


def _resolve_domain_name(item: dict, domain_by_prefix: dict[str, str], fallback: str = "—") -> str:
    explicit = _first(item.get("domain_name"), default="")
    if explicit:
        return str(explicit)
    domain_value = _first(item.get("domain"), default="")
    if domain_value and not _looks_like_code(domain_value):
        return str(domain_value)
    mapped = _infer_domain_from_code(
        _first(item.get("code"), domain_value, default=""),
        fallback="",
        domain_by_prefix=domain_by_prefix,
    )
    if mapped:
        return mapped
    return str(domain_value or fallback)


def _infer_l2_from_name(name: str) -> str:
    name = name or "待补测知识点"
    if "三角" in name or "圆" in name or "四边形" in name:
        return "平面图形"
    if "勾股" in name:
        return "图形关系"
    if "函数" in name:
        return "函数与图像"
    if "方程" in name or "不等式" in name:
        return "方程与不等式"
    if "统计" in name or "概率" in name:
        return "统计分析"
    if "数" in name or "运算" in name:
        return "数的概念与运算"
    return "核心模块"


def _domain_lookup_from_items(payload: dict) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for item in _get(payload, "domains.domain_items", []) or []:
        name = _first(item.get("domain_name"), item.get("name_cn"), item.get("name"), default="")
        if name:
            lookup[str(name)] = item
    return lookup


def _domain_node_position(index: int, total: int) -> dict[str, int]:
    """Return a stable node position around the blueprint ability map."""
    total = max(total, 1)
    angle = -math.pi / 2 + (2 * math.pi * index / total)
    return {
        "x": int(round(300 + 202 * math.cos(angle))),
        "y": int(round(292 + 234 * math.sin(angle))),
    }


def _domain_state(item: dict, panel: dict, target_accuracy: Any) -> tuple[str, Any]:
    accuracy = _first(item.get("accuracy_text"), item.get("accuracy"), default=None)
    has_data_value = _first(item.get("has_data"), panel.get("has_data"), default=None)
    has_data = bool(has_data_value) if has_data_value is not None else accuracy not in (None, "", "--", "—")
    status_text = str(_first(item.get("status_text"), item.get("status"), default=""))
    if "已达标" in status_text:
        return "achieved", accuracy
    if "关注" in status_text:
        return "attention", accuracy
    if "加强" in status_text or "提升" in status_text:
        return "improve", accuracy
    if "不足" in status_text or "无数据" in status_text:
        return "nodata", accuracy
    return _state_from_accuracy(accuracy, target_accuracy, has_data=has_data), accuracy


def _build_domains(payload: dict, target_accuracy: Any) -> list[dict]:
    raw_items = [item for item in (_get(payload, "domains.domain_items", []) or []) if isinstance(item, dict)]
    if raw_items:
        domains: list[dict] = []
        source_items = raw_items[:6]
        for idx, item in enumerate(source_items):
            state, accuracy = _domain_state(item, {}, target_accuracy)
            pos = _domain_node_position(idx, len(source_items))
            domains.append({
                "key": str(_first(item.get("code"), default=f"domain-{idx + 1}")),
                "name": _first(item.get("domain_name"), item.get("name_cn"), item.get("name"), default=f"领域{idx + 1}"),
                "icon": MATH_DOMAINS[idx % len(MATH_DOMAINS)][2],
                "state": state,
                "state_label": _state_label(state),
                "accuracy_text": _fmt_pct(accuracy, "—"),
                "x": pos["x"],
                "y": pos["y"],
            })
        return domains

    domain_lookup = _domain_lookup_from_items(payload)
    panels = _get(payload, "kp_drill.domain_panels", {}) or {}
    panel_by_name = {}
    if isinstance(panels, dict):
        for panel in panels.values():
            if isinstance(panel, dict) and panel.get("domain_name"):
                panel_by_name[panel["domain_name"]] = panel

    domains = []
    for idx, (key, default_name, icon) in enumerate(MATH_DOMAINS):
        item = domain_lookup.get(default_name, {})
        panel = panel_by_name.get(default_name, {})
        state, accuracy = _domain_state(item, panel, target_accuracy)
        pos = _domain_node_position(idx, len(MATH_DOMAINS))
        domains.append({
            "key": key,
            "name": default_name,
            "icon": icon,
            "state": state,
            "state_label": _state_label(state),
            "accuracy_text": _fmt_pct(accuracy, "—"),
            "x": pos["x"],
            "y": pos["y"],
        })
    return domains


def _build_city_focus(payload: dict, limit: int = 3) -> list[dict]:
    items = list(_get(payload, "city_compare.overlap_items", []) or [])
    items.sort(key=lambda it: (_num(it.get("city_rank"), 9999), -(_num(it.get("importance_score"), 0) or 0)))
    target = _first(_get(payload, "summary.target_accuracy"), _get(payload, "meta.target_accuracy"), default=85)
    domain_by_prefix = _domain_name_by_code_prefix(payload)
    focus = []
    for it in items[:limit]:
        acc = it.get("student_accuracy")
        if acc is None:
            state = "need_test"
            tag = "优先补测"
        elif (_pct_num(acc, 0) or 0) < (_pct_num(target, 85) or 85):
            state = "weak"
            tag = "高频+薄弱"
        else:
            state = "ok"
            tag = "保持巩固"
        focus.append({
            "rank": int(_num(it.get("city_rank"), len(focus) + 1) or (len(focus) + 1)),
            "name": _first(it.get("kp_name"), it.get("name_cn"), it.get("name"), default="高频考点"),
            "domain": _infer_domain_from_code(it.get("code"), fallback="—", domain_by_prefix=domain_by_prefix),
            "score": _fmt_score(it.get("importance_score")),
            "score_weight": _first(it.get("score_weight"), default=""),
            "student_accuracy_text": _fmt_pct(acc, "—"),
            "tag": tag,
            "state": state,
            "code": it.get("code", ""),
        })
    # keep layout stable if city data is empty
    while len(focus) < limit:
        idx = len(focus) + 1
        focus.append({
            "rank": idx,
            "name": "待补充城市考频数据",
            "domain": "—",
            "score": "—",
            "score_weight": "",
            "student_accuracy_text": "—",
            "tag": "待接入",
            "state": "need_test",
            "code": "",
        })
    return focus


def _normalize_weakness_item(item: dict, fallback_rank: int, domain_by_prefix: dict[str, str] | None = None) -> dict:
    priority = str(_first(item.get("priority"), item.get("priority_level"), item.get("level"), item.get("priority_text"), default="P2"))
    name = _first(
        item.get("name"),
        item.get("name_cn"),
        item.get("kp_name"),
        item.get("knowledge_point"),
        item.get("point"),
        default="待确认知识点",
    )
    domain = _resolve_domain_name(item, domain_by_prefix or {}, fallback="—")
    accuracy = _first(item.get("accuracy_text"), item.get("accuracy"), default=None)
    gap = _first(
        item.get("distance_text"),
        item.get("gap_to_target_text"),
        item.get("delta_vs_target_text"),
        item.get("gap_to_target"),
        item.get("delta_vs_target"),
        default=None,
    )
    city_rank = _first(item.get("city_rank_text"), item.get("city_rank"), item.get("rank"), default="—")
    raw_tags = item.get("tags")
    if isinstance(raw_tags, list):
        tags = raw_tags
    else:
        tags = [item.get("tag") or raw_tags] if (item.get("tag") or raw_tags) else []
    tag_text = " / ".join([str(t.get("text", t)) if isinstance(t, dict) else str(t) for t in tags[:2]])
    return {
        "priority": priority,
        "priority_class": _priority_class(priority),
        "name": name,
        "domain": domain,
        "accuracy_text": _fmt_pct(accuracy, "—"),
        "gap_text": _fmt_signed_pct(gap, "—"),
        "city_rank_text": f"top{city_rank}" if str(city_rank).isdigit() else str(city_rank),
        "tag_text": tag_text,
        "l2": _infer_l2_from_name(str(name)),
        "sort_key": (PRIORITY_ORDER.get(priority, 9), abs(_pct_num(gap, 0) or 0) * -1, fallback_rank),
    }


def _build_shortlist(payload: dict, city_focus: list[dict], limit: int = 4) -> list[dict]:
    items = []
    domain_by_prefix = _domain_name_by_code_prefix(payload)
    for idx, it in enumerate(_get(payload, "core_weakness.items", []) or []):
        if isinstance(it, dict):
            items.append(_normalize_weakness_item(it, idx, domain_by_prefix))
    if items:
        items.sort(key=lambda x: x["sort_key"])
        return items[:limit]

    # Fallback: no stable weakness list yet, so show high-frequency points to test.
    fallback = []
    for it in city_focus[:limit]:
        fallback.append({
            "priority": "补测",
            "priority_class": "test",
            "name": it["name"],
            "domain": it["domain"],
            "accuracy_text": "—",
            "gap_text": "待测",
            "city_rank_text": f"top{it['rank']}",
            "tag_text": it["tag"],
            "l2": _infer_l2_from_name(str(it["name"])),
            "sort_key": (4, 0, it["rank"]),
        })
    return fallback


def _confidence_info(payload: dict) -> dict:
    total_level = str(_first(_get(payload, "data_reliability.conclusion.total_level"), default="未知"))
    weighted = _num(_get(payload, "data_reliability.conclusion.conclusion_credibility.weighted_score"), None)
    if "高" in total_level:
        stars = 5
        class_name = "high"
    elif "中" in total_level:
        stars = 3
        class_name = "medium"
    elif "低" in total_level or "不足" in total_level:
        stars = 2
        class_name = "low"
    else:
        if weighted is None:
            stars = 3
            class_name = "medium"
        elif weighted >= 75:
            stars = 5
            class_name = "high"
        elif weighted >= 45:
            stars = 3
            class_name = "medium"
        else:
            stars = 2
            class_name = "low"
    return {
        "level": total_level,
        "weighted_score_text": _fmt_score(weighted, "—"),
        "stars": stars,
        "class_name": class_name,
        "message": _first(_get(payload, "data_reliability.conclusion.message"), default="结论可信度待确认"),
    }


def _active_axis_stage(payload: dict, shortlist: list[dict]) -> str:
    total_level = str(_first(_get(payload, "data_reliability.conclusion.total_level"), default=""))
    report_title = str(_first(_get(payload, "meta.report_title"), default=""))
    has_real_weakness = any(item.get("priority") != "补测" for item in shortlist)
    needs_more_data = "低" in total_level or "不足" in total_level
    if "追踪" in report_title or "阶段" in report_title:
        return "追踪复测"
    if has_real_weakness:
        return "老师执行"
    if needs_more_data:
        return "数据进入"
    return "AI诊断分析"


def _build_focus_paths(city_focus: list[dict], shortlist: list[dict], limit: int = 5) -> list[dict]:
    rows = []
    source = []
    for item in shortlist:
        source.append({"name": item["name"], "domain": item["domain"], "state": "need_test" if item["priority"] == "补测" else "improve"})
    for item in city_focus:
        if item["name"] not in {s["name"] for s in source}:
            source.append({"name": item["name"], "domain": item["domain"], "state": item["state"]})

    for idx, it in enumerate(source[:limit]):
        name = it["name"]
        domain = it.get("domain") or "待确认"
        l2 = _infer_l2_from_name(name)
        if it.get("state") == "need_test":
            l4 = "建议补测"
            state = "need_test"
        elif it.get("state") == "ok":
            l4 = "巩固保持"
            state = "achieved"
        else:
            l4 = "专项突破"
            state = "improve"
        rows.append({
            "domain": domain,
            "l2": l2,
            "l3": name,
            "l4": l4,
            "state": state,
            "state_label": _state_label(state),
        })
    while len(rows) < limit:
        rows.append({"domain": "—", "l2": "数据不足", "l3": "待补充样本", "l4": "未测", "state": "nodata", "state_label": "未测"})
    return rows


def _execution_task_copy(row: dict) -> dict[str, str]:
    """Convert a diagnostic focus item into teacher/student/tracking actions.

    The second blueprint should not repeat the first page's L1-L4 drill table.
    It uses the same diagnosis only as input, then renders execution actions.
    """
    state = str(row.get("state") or "improve")
    domain = str(row.get("domain") or "待确认")
    l2 = str(row.get("l2") or "")
    l3 = str(row.get("l3") or "待确认知识点")
    combined = f"{domain} {l2} {l3}"

    if state == "nodata" or domain == "—":
        return {
            "target": "补充样本",
            "focus": "先形成可判断证据",
            "teacher_action": "安排补测题组",
            "student_task": "完成基础样本",
            "tracking_signal": "样本覆盖可判读",
            "icon": "data",
        }
    if state == "need_test":
        return {
            "target": f"{domain}验证",
            "focus": l3,
            "teacher_action": "先补测确认",
            "student_task": "限时小测+订正",
            "tracking_signal": "确认是否专项",
            "icon": "question",
        }
    if state == "achieved":
        return {
            "target": f"{domain}巩固",
            "focus": l3,
            "teacher_action": "保持难度梯度",
            "student_task": "穿插复习题",
            "tracking_signal": "稳定在目标线",
            "icon": "shield",
        }

    if any(key in combined for key in ("全等", "判定")):
        teacher_action = "拆判定条件链"
        student_task = "画图推理+变式练"
        tracking_signal = "步骤表达达标"
        icon = "domain-geometry"
    elif "勾股" in combined:
        teacher_action = "建立直角模型"
        student_task = "应用题转图形"
        tracking_signal = "模型识别达标"
        icon = "domain-geometry"
    elif any(key in combined for key in ("几何", "图形", "三角")):
        teacher_action = "梳理图形关系"
        student_task = "条件标注+证明"
        tracking_signal = "推理链完整"
        icon = "domain-geometry"
    elif any(key in combined for key in ("代数", "方程", "不等式", "运算")):
        teacher_action = "定位运算错因"
        student_task = "分步演算+纠错"
        tracking_signal = "同类题回升"
        icon = "domain-algebra"
    elif "函数" in combined:
        teacher_action = "梳理变量关系"
        student_task = "读图识别+迁移"
        tracking_signal = "图像题稳定"
        icon = "domain-function"
    elif any(key in combined for key in ("统计", "概率")):
        teacher_action = "重建数据读法"
        student_task = "图表分析训练"
        tracking_signal = "信息提取达标"
        icon = "domain-statistics"
    else:
        teacher_action = "讲清关键方法"
        student_task = "专项练习+复盘"
        tracking_signal = "连续复测达标"
        icon = "target"

    return {
        "target": f"{domain}专项",
        "focus": l3,
        "teacher_action": teacher_action,
        "student_task": student_task,
        "tracking_signal": tracking_signal,
        "icon": icon,
    }


def _build_execution_tasks(focus_paths: list[dict], limit: int = 4) -> list[dict]:
    """Build task-oriented rows for the execution blueprint."""
    source = [row for row in focus_paths if row.get("state") != "nodata"] or focus_paths[:1]
    tasks = []
    for idx, row in enumerate(source[:limit], start=1):
        task = _execution_task_copy(row)
        task.update({
            "no": f"T{idx}",
            "state": row.get("state") or "improve",
            "state_label": row.get("state_label") or _state_label(row.get("state")),
        })
        tasks.append(task)
    return tasks


def _build_diagnostic_drill_rows(domains: list[dict], shortlist: list[dict], limit: int = 6) -> list[dict]:
    """Build a fuller L1-L4 drill table for the first blueprint reference page."""
    rows: list[dict] = []
    used_names: set[str] = set()

    for item in shortlist:
        if len(rows) >= limit:
            break
        name = str(item.get("name") or "待确认知识点")
        used_names.add(name)
        rows.append({
            "domain": item.get("domain") or "—",
            "l2": item.get("l2") or _infer_l2_from_name(name),
            "l3": name,
            "l4": item.get("tag_text") or "专项突破",
            "state": item.get("priority_class") or "p2",
        })

    used_domains = {str(row.get("domain")) for row in rows if row.get("domain") not in (None, "—")}
    for domain in domains:
        if len(rows) >= limit:
            break
        domain_name = str(domain.get("name") or "—")
        if domain_name in used_domains:
            continue
        state = str(domain.get("state") or "nodata")
        if state == "achieved":
            l4 = "保持巩固"
        elif state == "nodata":
            l4 = "待补测"
        elif state == "attention":
            l4 = "巩固提升"
        else:
            l4 = "专项突破"
        rows.append({
            "domain": domain_name,
            "l2": _infer_l2_from_name(domain_name),
            "l3": f"{domain_name}关键能力",
            "l4": l4,
            "state": state,
        })

    while len(rows) < limit:
        rows.append({"domain": "—", "l2": "数据不足", "l3": "待补充样本", "l4": "未测", "state": "nodata"})
    return rows


def _build_path_milestones(current_accuracy: Any, target_accuracy: Any) -> list[dict]:
    """Build the four-node diagnostic path shown on the page-2 timeline."""
    cur = _pct_num(current_accuracy, None)
    target = _pct_num(target_accuracy, 85) or 85
    if cur is None:
        cur = 0
    gap = max(target - cur, 0)
    first = min(target, cur + gap * 0.62)
    second = min(target, cur + gap * 0.85)
    return [
        {"value": _fmt_pct(round(cur)), "label": "当前水平", "state": "current"},
        {"value": _fmt_pct(round(first)), "label": "阶段目标1", "state": "foundation"},
        {"value": _fmt_pct(round(second)), "label": "阶段目标2", "state": "improve"},
        {"value": _fmt_pct(round(target)), "label": "目标线", "state": "target"},
    ]


def _build_stage_plan(payload: dict, shortlist: list[dict]) -> dict:
    cur = _pct_num(_first(_get(payload, "summary.current_accuracy"), _get(payload, "summary.current_accuracy_text"), default=None), None)
    target = _pct_num(_first(_get(payload, "summary.target_accuracy"), _get(payload, "meta.target_accuracy"), default=85), 85) or 85
    if cur is None:
        cur = 0
    gap = max(target - cur, 0)
    # Use conservative stage markers if no custom plan exists.
    s1 = min(target, cur + max(8, gap * 0.35))
    s2 = min(target, cur + max(15, gap * 0.70))
    s3 = target
    main_focus = "、".join([x["name"] for x in shortlist[:2] if x.get("name") and x.get("name") != "待补充样本"])
    if not main_focus:
        main_focus = "高频考点与样本覆盖"
    return {
        "current_text": _fmt_pct(cur),
        "target_text": _fmt_pct(target),
        "stages": [
            {
                "no": "第一阶段",
                "range": "0-30天",
                "title": "突破基础证据",
                "target_text": _fmt_pct(s1),
                "items": ["补齐数据缺口", f"优先处理：{main_focus}", "建立错因记录"],
                "state": "foundation",
            },
            {
                "no": "第二阶段",
                "range": "30-60天",
                "title": "巩固核心能力",
                "target_text": _fmt_pct(s2),
                "items": ["模块专项突破", "题型能力迁移", "错题深度复盘"],
                "state": "improve",
            },
            {
                "no": "第三阶段",
                "range": "60天+",
                "title": "冲刺目标线",
                "target_text": _fmt_pct(s3),
                "items": ["综合训练与真题演练", "阶段检测与反馈", "稳定冲刺目标"],
                "state": "sprint",
            },
        ],
    }


def _evidence(payload: dict) -> dict:
    raw = _first(_get(payload, "cover.cover_meta.raw_question_count"), default="—")
    valid = _first(_get(payload, "cover.cover_meta.display_question_count"), _get(payload, "cover.cover_meta.question_count"), _get(payload, "appendix.papers.total_questions"), default="—")
    expanded = _first(_get(payload, "question_detail.total_count"), _get(payload, "cover.cover_meta.total_questions"), default="—")
    paper_count = _first(_get(payload, "cover.cover_meta.paper_count"), _get(payload, "appendix.papers.total_papers"), default="—")
    stats = _get(payload, "data_reliability.section_4_coverage.stats", {}) or {}
    return {
        "raw_questions": _fmt_int(raw),
        "valid_questions": _fmt_int(valid),
        "expanded_questions": _fmt_int(expanded),
        "paper_count": _fmt_int(paper_count),
        "l2_coverage_text": _first(stats.get("l2_covered_text"), default=f"{_fmt_int(stats.get('l2_covered'))} / {_fmt_int(stats.get('l2_total'))}"),
        "l3_coverage_text": _first(stats.get("l3_covered_text"), default=f"{_fmt_int(stats.get('l3_covered'))} / {_fmt_int(stats.get('l3_total'))}"),
        "l1_total": _fmt_int(stats.get("l1_total"), "—"),
        "l2_total": _fmt_int(stats.get("l2_total"), "—"),
        "l3_total": _fmt_int(stats.get("l3_total"), "—"),
        "test_period": _first(stats.get("test_period"), default="—"),
        "summary_text": _first(_get(payload, "data_reliability.section_4_coverage.summary_text"), default="数据覆盖情况待确认。"),
    }


def _business_note(payload: dict, confidence: dict) -> str:
    if confidence["class_name"] == "low":
        return "当前更适合作为补测与补练依据，而不是直接做能力归因。"
    if confidence["class_name"] == "medium":
        return "当前已可初步定位方向，建议结合老师观察继续验证。"
    return "当前证据较充分，可进入薄弱点排序与补习方案制定。"


def build_learning_blueprints(payload: dict) -> dict[str, dict]:
    """Return {diagnostic_blueprint, execution_blueprint}."""
    evidence = _evidence(payload)
    target_accuracy = _first(_get(payload, "summary.target_accuracy"), _get(payload, "meta.target_accuracy"), default=85)
    domains = _build_domains(payload, target_accuracy)
    city_focus = _build_city_focus(payload, limit=3)
    shortlist = _build_shortlist(payload, city_focus, limit=4)
    confidence = _confidence_info(payload)
    active_stage = _active_axis_stage(payload, shortlist)
    stage_plan = _build_stage_plan(payload, shortlist)
    focus_paths = _build_focus_paths(city_focus, shortlist, limit=5)
    execution_tasks = _build_execution_tasks(focus_paths, limit=4)
    diagnostic_drill_rows = _build_diagnostic_drill_rows(domains, shortlist, limit=6)

    student_name = _first(_get(payload, "meta.student_display_name"), default="学生")
    grade = _first(_get(payload, "meta.grade"), _get(payload, "cover.cover_meta.grade"), default="—")
    subject_name = _first(_get(payload, "meta.subject_name"), default="—")
    subject_key = str(_first(_get(payload, "meta.subject"), subject_name, default="")).lower()
    subject_label = subject_name if subject_name != "—" else "学科"
    is_math = subject_key in {"math", "数学"} or subject_name == "数学"
    city_name = _first(_get(payload, "meta.city_name"), _get(payload, "cover.cover_meta.city_name"), _get(payload, "cover.cover_meta.city"), default="—")
    report_title = _first(_get(payload, "meta.report_title"), _get(payload, "meta.report_name"), default="学情诊断报告")
    target_score_text = _first(_get(payload, "summary.target_score_text"), f"{_get(payload, 'meta.target_score', '—')}分+", default="—")
    current_accuracy_text = _first(_get(payload, "summary.current_accuracy_text"), _fmt_pct(_get(payload, "summary.current_accuracy")), default="—")
    target_accuracy_text = _first(_get(payload, "summary.target_accuracy_text"), _fmt_pct(target_accuracy), default="—")
    delta_text = _first(_get(payload, "summary.current_delta_text"), default="—")
    path_milestones = _build_path_milestones(current_accuracy_text, target_accuracy_text)

    meta = {
        "student_name": student_name,
        "grade": grade,
        "subject_name": subject_name,
        "city_name": city_name,
        "report_title": report_title,
        "target_score_text": target_score_text,
        "report_date": _first(_get(payload, "meta.report_date"), _get(payload, "cover.cover_meta.report_date"), default="—"),
        "report_id": _first(_get(payload, "meta.report_id"), default="—"),
        "ability_map_title": f"{subject_label}能力中轴图",
        "ability_map_aria": f"{subject_label}能力中轴图",
        "ability_axis_label": f"{subject_label}能力中轴",
        "l1_label": "L1 六大领域" if is_math else "L1 能力领域",
        "page1_label": "第1页 / 共2页",
        "page2_label": "第2页 / 共2页",
    }

    diagnostic = {
        "meta": meta,
        "headline": {
            "title": "学生学情诊断全景蓝图",
            "subtitle": "看清当前水平、核心短板与目标差距",
            "slogan": "不是只看错了多少题，而是看清真正影响提分的结构性问题。",
        },
        "profile": {
            "student_name": student_name,
            "grade": grade,
            "city_name": city_name,
            "subject_name": subject_name,
            "current_accuracy_text": current_accuracy_text,
            "target_accuracy_text": target_accuracy_text,
            "delta_text": delta_text,
            "stage_name": _first(_get(payload, "tiered_learning.module.cards.stage_judgement.current.stage_name"), default="待确认"),
            "stage_hint": _first(_get(payload, "tiered_learning.module.cards.stage_judgement.current.position_hint"), default="根据数据持续更新"),
            "focus_domains_text": "、".join(sorted({x["domain"] for x in shortlist[:3] if x.get("domain") and x.get("domain") != "—"})) or "待补测",
            "path_milestones": path_milestones,
        },
        "domains": domains,
        "shortlist": shortlist,
        "diagnostic_drill_rows": diagnostic_drill_rows,
        "city_focus": city_focus,
        "stage_plan": stage_plan,
        "evidence": evidence,
        "confidence": confidence,
        "note": _business_note(payload, confidence),
        "footer": {
            "left": f"报告日期：{meta['report_date']}",
            "middle": "本页为诊断概览（第1页，共2页）",
            "right": f"报告编号：{meta['report_id']}",
        },
    }

    execution = {
        "meta": meta,
        "headline": {
            "title": "补习执行与追踪蓝图",
            "subtitle": "把诊断结果转化为老师可执行的补习路线",
            "slogan": "AI负责诊断，老师负责执行，系统负责持续追踪，三方协同让进步可见、可量化。",
        },
        "focus_paths": focus_paths,
        "execution_tasks": execution_tasks,
        "stage_plan": stage_plan,
        "evidence": evidence,
        "confidence": confidence,
        "data_engine": {
            "paper_count": evidence["paper_count"],
            "valid_questions": evidence["valid_questions"],
            "expanded_questions": evidence["expanded_questions"],
            "domain_modules": evidence["l2_total"],
            "period": evidence["test_period"],
            "reliability_level": confidence["level"],
            "stars": confidence["stars"],
            "pipeline": ["数据采集", "清洗整合", "特征提取", "AI建模分析", "结果输出"],
            "source_text": "数据来源：学生练习记录、模拟测试与专项训练。",
            "warning_text": evidence["summary_text"],
        },
        "support_system": {
            "teacher_items": ["精准诊断", "定制计划", "学情跟踪", "策略指导"],
            "parent_items": ["了解学情", "监督执行", "鼓励支持", "配合学校"],
            "student_items": ["了解薄弱点", "每日练习", "错题整理", "定期回顾"],
            "summary": "了解学情、配合练习、持续巩固，让学习进步更明显。",
        },
        "axis": {
            "active_stage": active_stage,
            "stages": [
                {"name": "数据进入", "desc": "试卷收集与上传", "icon": "data"},
                {"name": "AI诊断分析", "desc": "多维数据建模分析", "icon": "ai"},
                {"name": "老师执行", "desc": "制定计划并落地", "icon": "teacher"},
                {"name": "追踪复测", "desc": "阶段检测与反馈", "icon": "track"},
                {"name": "专项突破", "desc": "持续优化与提分", "icon": "rocket"},
            ],
        },
        "footer": {
            "left": "温馨提示：建议每2-4周进行一次阶段性检测。",
            "right": f"报告生成时间：{meta['report_date']}",
        },
    }

    return {"diagnostic_blueprint": diagnostic, "execution_blueprint": execution}
