"""
engine.py — 主入口
===================
payload → 分析 → 排版 → CSS

支持两种模式：
1. 双 Pass（推荐）: 预渲染 HTML → Playwright 测量 DOM 高度 → 精确排版
2. 单 Pass（回退）: payload 经验估算 → 近似排版

集成到 render_standalone.py:
    # 双 Pass（推荐）
    css = build_typeset_css(payload, measured=measured_heights)
    # 单 Pass（回退）
    css = build_typeset_css(payload)
"""
from __future__ import annotations
from typing import Dict, Optional
from .math_func import PageLayout, layout_page
from .payload_analyzer import ANALYZERS, analyze_with_measured
from .css_builder import build_css


def build_typeset_css(payload: dict,
                      measured: Optional[dict[str, list[tuple[str, float]]]] = None
                      ) -> str:
    """生成排版 CSS。

    Args:
        payload: 渲染数据
        measured: Pass 1 DOM 测量结果 {mod_id: [(key, height_mm), ...]}
                  None 时回退到经验估算
    """
    if measured:
        block_map = analyze_with_measured(payload, measured)
    else:
        block_map = {}
        for mod_id, analyzer in ANALYZERS.items():
            blocks = analyzer(payload)
            if blocks:
                block_map[mod_id] = blocks

    layouts: Dict[str, PageLayout] = {}
    for mod_id, blocks in block_map.items():
        if blocks:
            layouts[mod_id] = layout_page(blocks)

    return build_css(layouts)
