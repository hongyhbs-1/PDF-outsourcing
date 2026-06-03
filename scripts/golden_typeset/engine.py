"""
engine.py -- main entry point
==============================
payload -> analysis -> typeset -> CSS

Supports two modes:
1. Dual Pass (recommended): pre-render HTML -> Playwright measures DOM heights -> precise typeset
2. Single Pass (fallback): payload empirical estimation -> approximate typeset

Integration into render_standalone.py:
    # Dual Pass (recommended)
    css = build_typeset_css(payload, measured=measured_heights)
    # Single Pass (fallback)
    css = build_typeset_css(payload)

LayoutProfile integration:
    css = build_typeset_css(payload, layout_profile=lp)
    # Or auto-compute from payload:
    css = build_typeset_css(payload, auto_profile=True)
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
                      auto_profile: bool = False,
                      ) -> str:
    """Generate typeset CSS.

    Args:
        payload: render data
        measured: Pass 1 DOM measurement results {mod_id: [(key, height_mm), ...]}
                  None falls back to empirical estimation
        layout_profile: optional LayoutProfile for CSS variable injection
        auto_profile: when True and layout_profile is None, auto-compute
                      DataProfile -> LayoutProfile from payload
    """
    # Auto-compute LayoutProfile if requested and not explicitly provided
    if layout_profile is None and auto_profile:
        try:
            from .data_profile import compute_data_profile
            from .layout_profile import compute_layout_profile
            dp = compute_data_profile(payload)
            layout_profile = compute_layout_profile(dp)
        except Exception:
            # Non-fatal: profile computation failure should not break typesetting
            layout_profile = None

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
