"""
engine.py -- main entry point
==============================
payload -> analysis -> typeset -> CSS

Supports two modes:
1. Dual Pass (recommended): pre-render HTML -> Playwright measures DOM heights -> precise typeset
2. Single Pass (fallback): payload empirical estimation -> approximate typeset

LayoutProfile integration:
    layout_profile = compute_layout_profile(compute_data_profile(payload))
    css = build_typeset_css(payload, measured=measured_heights, layout_profile=layout_profile)
"""
from __future__ import annotations
from dataclasses import replace as _dc_replace
from typing import Dict, Optional, TYPE_CHECKING
from .math_func import Block, PageLayout, layout_page, golden_gaps, CANVAS_H
from .payload_analyzer import ANALYZERS, analyze_with_measured
from .css_builder import build_css

if TYPE_CHECKING:
    from scripts.contracts.render_payload import RenderPayload
    from .layout_profile import LayoutProfile


def build_typeset_css(payload: RenderPayload,
                      measured: Optional[dict[str, list[tuple[str, float]]]] = None,
                      layout_profile: Optional[LayoutProfile] = None,
                      ) -> str:
    """Generate typeset CSS.

    Args:
        payload: render data
        measured: Pass 1 DOM measurement results {mod_id: [(key, height_mm), ...]}
                  None falls back to empirical estimation
        layout_profile: optional LayoutProfile for CSS variable injection
    """
    # 始终计算经验估算 ratio（用于密度决策）
    empirical_blocks: Dict[str, list] = {}
    for mod_id, analyzer in ANALYZERS.items():
        blocks = analyzer(payload)
        if blocks:
            empirical_blocks[mod_id] = blocks

    empirical_layouts: Dict[str, PageLayout] = {}
    for mod_id, blocks in empirical_blocks.items():
        if blocks:
            empirical_layouts[mod_id] = layout_page(blocks)

    # measured 数据用于精确内容高度，但间距和密度决策用经验估算 ratio
    if measured:
        block_map = analyze_with_measured(payload, measured)
    else:
        block_map = empirical_blocks

    layouts: Dict[str, PageLayout] = {}
    for mod_id, blocks in block_map.items():
        if blocks:
            layouts[mod_id] = layout_page(blocks)

    # 用经验估算 ratio 重新计算间距（measured ratio 含间距偏高，导致 u_max 过大）
    for mod_id, emp_layout in empirical_layouts.items():
        if mod_id in layouts:
            layout = layouts[mod_id]
            emp_ratio = emp_layout.content_ratio
            n = len(layout.blocks)
            remaining = CANVAS_H - layout.content_h
            gaps_raw = golden_gaps(remaining, n, content_ratio=emp_ratio)
            top_pad = gaps_raw[0]
            bottom_pad = gaps_raw[-1]
            inter = gaps_raw[1:-1]
            gaps = [top_pad] + inter

            # 重新定位 blocks
            y = 0.0
            new_blocks = []
            for i, blk in enumerate(layout.blocks):
                y += gaps[i]
                new_blocks.append(Block(key=blk.key, h=blk.h,
                                        gap=round(gaps[i], 2), y=round(y, 2)))
                y += blk.h

            layouts[mod_id] = _dc_replace(
                layout,
                blocks=new_blocks,
                gaps_h=round(sum(gaps), 2),
                top_pad=round(top_pad, 2),
                bottom_pad=round(bottom_pad, 2),
                unit_u=round(top_pad, 4),
                content_ratio=emp_ratio,
            )

    # M9 split: skip golden_typeset when splitter handles pagination
    try:
        from m9_splitter import should_split_m9
        if should_split_m9(payload):
            layouts.pop("m9", None)
            empirical_blocks.pop("m9", None)
    except ImportError:
        pass

    return build_css(layouts, layout_profile=layout_profile)
