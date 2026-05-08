"""
payload_analyzer.py — payload → [(key, natural_height)]
========================================================
每个模块的分析器: 从 payload 提取字符数/字段数 → V() 估算高度。
"""
from __future__ import annotations
from typing import List
from .math_func import content_height, F_BODY, F_SMALL, F_TABLE


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


def m1(p):
    s = p.get("summary", {})
    kf = p.get("key_findings", [])
    bt = p.get("breakthrough", {})
    bti = bt.get("items", []) if isinstance(bt, dict) else []
    sg = p.get("suggestion", {})
    return [
        ("banner",   _h(F_BODY,  _c(s.get("banner_text","")), 0)),
        ("kpi",      _h(F_SMALL, 0, 3 + _len(s.get("pass_segments",[])))),
        ("findings", _h(F_BODY,  _sc(kf), _len(kf))),
        ("bt",       _h(F_BODY,  _sc(bti,"name_cn"), _len(bti))),
        ("suggest",  _h(F_BODY,  _c(sg.get("text","") if isinstance(sg,dict) else ""), 0)),
    ]

def m2(p):
    cw = p.get("core_weakness",{})
    items = cw.get("items",[]) if isinstance(cw,dict) else []
    tips = cw.get("tips",[]) if isinstance(cw,dict) else []
    return [
        ("intro", 15.0),
        ("table", _h(F_TABLE, _sc(items,"name_cn","reason"), _len(items))),
        ("tips",  _h(F_SMALL, _sc(tips), _len(tips))),
    ]

def m3(p):
    kd = p.get("kp_drill",{})
    tables = kd.get("tables",{}) if isinstance(kd,dict) else {}
    if isinstance(tables, list):
        n_levels = len(tables)
    elif isinstance(tables, dict):
        n_levels = sum(1 for k in ("l1","l2","l3","l4") if tables.get(k))
    else:
        n_levels = 1
    return [("drill", _h(F_TABLE, 0, max(n_levels, 1) * 3))]

def m4(p):
    d = p.get("domains",{})
    di = d.get("domain_items",[]) if isinstance(d,dict) else []
    return [
        ("meta",    12.0),
        ("legend",  10.0),
        ("charts",  _h(F_TABLE, 0, _len(di))),
        ("summary", _h(F_BODY,  _c(d.get("note_text","") if isinstance(d,dict) else ""), 0)),
    ]

def m5(p):
    cc = p.get("city_compare",{})
    oi = cc.get("overlap_items",[]) if isinstance(cc,dict) else []
    adv = cc.get("advice",[]) if isinstance(cc,dict) else []
    return [
        ("banner", 20.0),
        ("cards",  _h(F_BODY, 0, _len(oi))),
        ("table",  _h(F_TABLE, 0, _len(oi))),
        ("advice", _h(F_BODY, _sc(adv), _len(adv))),
    ]

def m6(p):
    tl = p.get("tiered_learning",{})
    mod = tl.get("module", tl) if isinstance(tl,dict) else {}
    tiers = mod.get("tiers",[]) if isinstance(mod,dict) else []
    cards = sum(len(t.get("cards",[])) if isinstance(t.get("cards",[]),list) else 1
                for t in (tiers or []) if isinstance(t,dict))
    return [("focus",20.0), ("tiers",_h(F_BODY,0,max(cards,3)))]

def m7(p):
    return [("boxes", _h(F_BODY, 0, 3))]

def m9(p):
    return [("content", _h(F_TABLE, 0, 5))]


ANALYZERS = {"m1":m1, "m2":m2, "m3":m3, "m4":m4,
             "m5":m5, "m6":m6, "m7":m7, "m9":m9}
