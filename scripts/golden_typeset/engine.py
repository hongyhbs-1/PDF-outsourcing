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
from typing import Dict, Optional, TYPE_CHECKING
from .math_func import PageLayout, layout_page
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

    # measured 数据用于精确间距，但密度决策用经验估算
    if measured:
        block_map = analyze_with_measured(payload, measured)
    else:
        block_map = empirical_blocks

    layouts: Dict[str, PageLayout] = {}
    for mod_id, blocks in block_map.items():
        if blocks:
            layouts[mod_id] = layout_page(blocks)

    # 用经验估算 ratio 覆盖 measured ratio（密度决策不受间距影响）
    from dataclasses import replace as _dc_replace
    for mod_id, emp_layout in empirical_layouts.items():
        if mod_id in layouts:
            layouts[mod_id] = _dc_replace(
                layouts[mod_id],
                content_ratio=emp_layout.content_ratio
            )

    return build_css(layouts, layout_profile=layout_profile)
