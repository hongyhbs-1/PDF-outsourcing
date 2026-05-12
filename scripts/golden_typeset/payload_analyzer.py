"""
payload_analyzer.py — payload → [(key, natural_height)]
========================================================
双 Pass 架构：
  Pass 1: 预渲染 HTML → Playwright 测量真实 DOM 高度
  Pass 2: 用测量值生成精确排版 CSS

回退：如果无法测量（无 Playwright），使用经验估算。
"""
from __future__ import annotations
from . import WRAPPER_SELECTORS
from .math_func import content_height, F_BODY, F_SMALL, F_TABLE, ROW_TABLE, ROW_ANALYSIS, ROW_CHECKLIST

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _len(o) -> float:
    return float(len(o)) if isinstance(o, (list, tuple)) else 0.0

def _c(o) -> float:
    return float(len(o)) if isinstance(o, str) else 0.0

def _sc(items, *keys) -> float:
    t = 0.0
    for it in (items or []):
        if isinstance(it, str): t += len(it)
        elif isinstance(it, dict):
            for k in keys:
                v = it.get(k, "")
                if isinstance(v, str): t += len(v)
    return t

def _h(f, c, fc, **kw) -> float:
    return content_height(f, c, fc, **kw)

# ---------------------------------------------------------------------------
# DOM 测量（Pass 1）
# ---------------------------------------------------------------------------

_MEASURE_JS = """(sel) => {
    const pxToMm = 96 / 25.4;
    const wrapper = document.querySelector(sel);
    if (!wrapper) return [];
    return Array.from(wrapper.children).map(c => c.getBoundingClientRect().height / pxToMm);
}"""


def measure_dom_heights(page) -> dict[str, list[tuple[str, float]]]:
    """Pass 1: 用 Playwright 测量每个模块 wrapper 直接子元素的真实高度。"""
    results = {}
    for mid, sel in WRAPPER_SELECTORS.items():
        heights = page.evaluate(_MEASURE_JS, sel)
        if heights and sum(heights) > 0:
            results[mid] = [(f"child_{i}", h) for i, h in enumerate(heights)]
    return results


# ---------------------------------------------------------------------------
# 经验估算（回退）
# ---------------------------------------------------------------------------

TITLE_HEIGHTS = {
    "m1": 20.0, "m2": 20.0, "m3": 0.0, "m4": 17.0,
    "m5": 23.0, "m6": 9.0, "m7": 10.0, "m9": 10.0,
}


def _estimate_m1(p):
    s = p.get("summary", {})
    kf = p.get("key_findings", [])
    bt = p.get("breakthrough", {})
    bti = bt.get("items", []) if isinstance(bt, dict) else []
    sg = p.get("suggestion", {})
    banner_h = _h(F_BODY, _c(s.get("banner_text", "")), 0)
    kpi_h = _h(F_SMALL, 0, 3 + _len(s.get("pass_segments", [])))
    findings_h = _h(F_BODY, _sc(kf), _len(kf))
    bt_h = _h(F_BODY, _sc(bti, "name_cn"), _len(bti))
    suggest_h = _h(F_BODY, _c(sg.get("text", "") if isinstance(sg, dict) else ""), 0)
    # CSS padding/margin 补偿: module-content-card padding + section bars + internal margins
    css_overhead = 32.0
    content_h = banner_h + kpi_h + findings_h + bt_h + suggest_h + css_overhead
    return [("title", TITLE_HEIGHTS["m1"]), ("content", content_h)]

def _estimate_m2(p):
    cw = p.get("core_weakness", {})
    items = cw.get("items", []) if isinstance(cw, dict) else []
    tips = cw.get("tips", []) if isinstance(cw, dict) else []
    return [("title", TITLE_HEIGHTS["m2"]), ("underline", 0.0),
            ("content", _h(3.2, _sc(items, "name_cn", "reason"), _len(items)) + _h(3.0, _sc(tips), _len(tips)))]

def _estimate_m3(p):
    """M3 知识点短板钻取 — 按实际领域数和表行数估算。"""
    drill = p.get("kp_drill", p.get("m3_kp_drill", {}))
    if not isinstance(drill, dict):
        return [("title", 0.0), ("content", 150.0)]

    domains = drill.get("domains", [])
    n_domains = len(domains) if isinstance(domains, list) else 6

    # 标题 + 简介 + 步骤
    intro_h = 28.0

    # 每个领域面板: header(8mm) + L2表(预估) + L3表(预估) + L4表(预估)
    total_rows = 0
    for d in (domains if isinstance(domains, list) else []):
        if not isinstance(d, dict):
            continue
        for level_key in ("l2_items", "l3_items", "l4_items"):
            items = d.get(level_key, [])
            total_rows += len(items) if isinstance(items, list) else 3

    # 如果无具体数据，用经验默认值
    if total_rows == 0:
        total_rows = n_domains * 6  # 每领域约6行

    panel_h = n_domains * 12.0 + total_rows * ROW_TABLE
    content_h = intro_h + panel_h + 16.0  # 16mm padding/margin

    return [("title", 0.0), ("content", min(content_h, 250.0))]

def _estimate_m4(p):
    d = p.get("domains", {})
    di = d.get("domain_items", []) if isinstance(d, dict) else []
    return [("title", TITLE_HEIGHTS["m4"]),
            ("content", 12.0 + _h(F_TABLE, 0, _len(di)) + _h(F_BODY, _c(d.get("note_text", "") if isinstance(d, dict) else ""), 0))]

def _estimate_m5(p):
    cc = p.get("city_compare", {})
    oi = cc.get("overlap_items", []) if isinstance(cc, dict) else []
    adv = cc.get("advice", []) if isinstance(cc, dict) else []
    return [("title", TITLE_HEIGHTS["m5"]),
            ("content", _h(F_BODY, 0, _len(oi)) + _h(F_TABLE, 0, _len(oi)) + _h(F_BODY, _sc(adv), _len(adv)))]

def _estimate_m6(p):
    return [("title", TITLE_HEIGHTS["m6"]), ("content", 210.0)]

def _estimate_m7(p):
    return [("title", TITLE_HEIGHTS["m7"]), ("content", 220.0)]

def _estimate_m9(p):
    qd = p.get("question_detail", {}) if isinstance(p, dict) else {}
    papers = qd.get("papers", []) if isinstance(qd, dict) else []
    if not isinstance(papers, list) or len(papers) == 0:
        return []
    content_h = 30.0
    for paper in papers:
        if not isinstance(paper, dict): continue
        wq = paper.get("wrong_questions", [])
        if isinstance(wq, list) and len(wq) > 0:
            for q in wq:
                content_h += 12.0 if isinstance(q, dict) and (q.get("error_analysis", "") or q.get("key_points", "")) else 7.0
            content_h += 12.0
        cq = paper.get("correct_questions", [])
        if isinstance(cq, list) and len(cq) > 0:
            content_h += 12.0 + len(cq) * ROW_TABLE
    return [("title", TITLE_HEIGHTS["m9"]), ("content", content_h)]

_ESTIMATORS = {
    "m1": _estimate_m1, "m2": _estimate_m2, "m3": _estimate_m3, "m4": _estimate_m4,
    "m5": _estimate_m5, "m6": _estimate_m6, "m7": _estimate_m7, "m9": _estimate_m9,
}


# ---------------------------------------------------------------------------
# 主接口
# ---------------------------------------------------------------------------

def analyze_with_measured(payload: dict, measured: dict[str, list[tuple[str, float]]]) -> dict[str, list[tuple[str, float]]]:
    """优先使用 DOM 测量值，回退到估算。"""
    results = {}
    for mid in WRAPPER_SELECTORS:
        if mid in measured and measured[mid]:
            results[mid] = measured[mid]
        elif mid in _ESTIMATORS:
            results[mid] = _ESTIMATORS[mid](payload)
    return results


# 兼容旧接口
def get_analyzers():
    """返回估算分析器（兼容 engine.py 旧接口）。"""
    return _ESTIMATORS

# 旧接口兼容
ANALYZERS = _ESTIMATORS
