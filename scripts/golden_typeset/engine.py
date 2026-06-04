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

    return build_css(layouts, layout_profile=layout_profile)
