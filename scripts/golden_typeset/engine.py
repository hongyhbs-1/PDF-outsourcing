"""
engine.py — 主入口
===================
payload → 分析 → 排版 → CSS

集成到 render_standalone.py (改 2 行):
    from golden_typeset.engine import build_typeset_css
    context["combined_css"] = load_css() + build_typeset_css(payload)
"""
from __future__ import annotations
from typing import Dict
from .math_func import PageLayout, layout_page
from .payload_analyzer import ANALYZERS
from .css_builder import build_css


def build_typeset_css(payload: dict) -> str:
    layouts: Dict[str, PageLayout] = {}
    for mod_id, analyzer in ANALYZERS.items():
        heights = analyzer(payload)
        if heights:
            layouts[mod_id] = layout_page(heights)
    return build_css(layouts)
