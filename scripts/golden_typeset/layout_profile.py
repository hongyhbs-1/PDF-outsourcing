"""
layout_profile.py -- L2: typesetting decisions depending on DataProfile
========================================================================
Maps a DataProfile to a LayoutProfile that controls spacing mode,
typography scale, padding, grid, and CSS variable overrides.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .data_profile import DataProfile


@dataclass
class LayoutProfile:
    """L2 typesetting decision profile."""

    spacing_mode: Literal["golden", "compact", "spacious"]
    typography_scale: float  # 0.80 - 1.00
    padding_scale: float  # 0.50 - 1.00
    grid_columns: int  # 1, 2, 3
    grid_gap_mm: float  # 3.0 - 8.0
    page_strategy: Literal["single", "flow", "natural", "center"]
    css_overrides: dict[str, str]  # CSS vars injected into :root
    module_overrides: dict[str, dict] = field(default_factory=dict)  # per-module overrides (e.g. {"m3": {"grid_columns": 2}})


# ---------------------------------------------------------------------------
# Mapping rules (subject + density -> base profile)
# ---------------------------------------------------------------------------

_BASE_PROFILES: dict[tuple[str, str], dict] = {
    # math profiles
    ("math", "dense"): {
        "spacing_mode": "compact",
        "typography_scale": 0.85,
        "padding_scale": 0.60,
        "grid_columns": 1,
        "grid_gap_mm": 3.5,
        "page_strategy": "single",
    },
    ("math", "normal"): {
        "spacing_mode": "golden",
        "typography_scale": 0.92,
        "padding_scale": 0.80,
        "grid_columns": 1,
        "grid_gap_mm": 5.0,
        "page_strategy": "single",
    },
    ("math", "sparse"): {
        "spacing_mode": "spacious",
        "typography_scale": 1.00,
        "padding_scale": 1.00,
        "grid_columns": 1,
        "grid_gap_mm": 6.0,
        "page_strategy": "single",
    },
    # english profiles
    ("english", "dense"): {
        "spacing_mode": "compact",
        "typography_scale": 0.85,
        "padding_scale": 0.65,
        "grid_columns": 2,
        "grid_gap_mm": 3.5,
        "page_strategy": "flow",
    },
    ("english", "normal"): {
        "spacing_mode": "golden",
        "typography_scale": 0.92,
        "padding_scale": 0.80,
        "grid_columns": 2,
        "grid_gap_mm": 5.0,
        "page_strategy": "single",
    },
    ("english", "sparse"): {
        "spacing_mode": "spacious",
        "typography_scale": 1.00,
        "padding_scale": 1.00,
        "grid_columns": 2,
        "grid_gap_mm": 8.0,
        "page_strategy": "single",
    },
}

# Module-level overrides for specific modules that need different treatment
_MODULE_OVERRIDES: dict[str, dict] = {
    "m3": {
        "spacing_mode": "compact",
        "typography_scale": 0.82,
        "padding_scale": 0.55,
        "grid_columns": 2,
        "grid_gap_mm": 3.0,
        "page_strategy": "natural",
    },
    "m9": {
        "spacing_mode": "compact",
        "typography_scale": 0.80,
        "padding_scale": 0.50,
        "grid_columns": 1,
        "grid_gap_mm": 3.0,
        "page_strategy": "natural",
    },
}


def _build_css_overrides(
    spacing_mode: str,
    typography_scale: float,
    padding_scale: float,
    grid_gap_mm: float,
) -> dict[str, str]:
    """Generate CSS variable overrides based on spacing mode and scales."""
    overrides: dict[str, str] = {}

    # Module padding scales with padding_scale
    base_padding_v = 16.0
    base_padding_h = 20.0
    scaled_pv = round(base_padding_v * padding_scale)
    scaled_ph = round(base_padding_h * padding_scale)
    overrides["--module-padding"] = f"{scaled_pv}px {scaled_ph}px"

    # Section gap
    base_section_gap = 12.0
    if spacing_mode == "compact":
        overrides["--section-gap"] = "8px"
    elif spacing_mode == "spacious":
        overrides["--section-gap"] = "16px"
    else:
        overrides["--section-gap"] = f"{round(base_section_gap * padding_scale)}px"

    # Card padding
    base_card_pv = 14.0
    base_card_ph = 18.0
    scaled_cpv = round(base_card_pv * padding_scale)
    scaled_cph = round(base_card_ph * padding_scale)
    overrides["--card-padding"] = f"{scaled_cpv}px {scaled_cph}px"

    # Table row height
    if spacing_mode == "compact":
        overrides["--table-row-height"] = "6.5mm"
    elif spacing_mode == "spacious":
        overrides["--table-row-height"] = "8.0mm"
    else:
        overrides["--table-row-height"] = "7.0mm"

    # Typography scale
    overrides["--typography-scale"] = f"{typography_scale:.2f}"

    # Padding scale
    overrides["--padding-scale"] = f"{padding_scale:.2f}"

    # Grid gap
    overrides["--grid-gap"] = f"{grid_gap_mm:.1f}mm"

    return overrides


def compute_layout_profile(
    data_profile: DataProfile,
    mod_id: str | None = None,
) -> LayoutProfile:
    """Derive a LayoutProfile from a DataProfile.

    Args:
        data_profile: L1 data feature snapshot.
        mod_id: Optional module ID for per-module overrides (e.g. "m3", "m9").
                When provided, module-specific overrides take precedence.

    Returns:
        LayoutProfile with spacing, typography, grid, and CSS variable decisions.
    """
    # Check module-level overrides first
    if mod_id and mod_id in _MODULE_OVERRIDES:
        base = _MODULE_OVERRIDES[mod_id]
    else:
        key = (data_profile.subject, data_profile.density)
        base = _BASE_PROFILES.get(key, _BASE_PROFILES[("math", "normal")])

    spacing_mode = base["spacing_mode"]
    typography_scale = base["typography_scale"]
    padding_scale = base["padding_scale"]
    grid_columns = base["grid_columns"]
    grid_gap_mm = base["grid_gap_mm"]
    page_strategy = base["page_strategy"]

    css_overrides = _build_css_overrides(
        spacing_mode, typography_scale, padding_scale, grid_gap_mm
    )

    # Build module_overrides: include all _MODULE_OVERRIDES entries that
    # differ from the base profile values.  This allows css_builder to
    # emit per-module CSS rules (e.g. grid_columns for m3).
    module_overrides: dict[str, dict] = {}
    for mid, overrides in _MODULE_OVERRIDES.items():
        diffs: dict = {}
        if overrides.get("grid_columns") != grid_columns:
            diffs["grid_columns"] = overrides["grid_columns"]
        if overrides.get("grid_gap_mm") != grid_gap_mm:
            diffs["grid_gap_mm"] = overrides["grid_gap_mm"]
        if overrides.get("typography_scale") != typography_scale:
            diffs["typography_scale"] = overrides["typography_scale"]
        if overrides.get("padding_scale") != padding_scale:
            diffs["padding_scale"] = overrides["padding_scale"]
        if diffs:
            module_overrides[mid] = diffs

    return LayoutProfile(
        spacing_mode=spacing_mode,
        typography_scale=typography_scale,
        padding_scale=padding_scale,
        grid_columns=grid_columns,
        grid_gap_mm=grid_gap_mm,
        page_strategy=page_strategy,
        css_overrides=css_overrides,
        module_overrides=module_overrides,
    )
