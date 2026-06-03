"""
data_profile.py -- L1: pure data feature extraction
====================================================
Extracts a DataProfile from a render payload, capturing
content density, feature flags, and per-module volume estimates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .math_func import CANVAS_H
from .payload_analyzer import _ESTIMATORS

if TYPE_CHECKING:
    from scripts.contracts.render_payload import RenderPayload


@dataclass
class DataProfile:
    """L1 data feature snapshot derived from payload."""

    subject: Literal["math", "english"]
    density: Literal["sparse", "normal", "dense"]
    content_volume: dict[str, float]  # {mod_id: estimated_mm}
    has_weakness: bool
    has_city_compare: bool
    has_composition: bool
    has_reading_deep: bool
    domain_count: int
    weakness_count: int
    total_kp: int


def compute_data_profile(payload: RenderPayload) -> DataProfile:
    """Derive a DataProfile from a render payload.

    Uses _ESTIMATORS from payload_analyzer to compute per-module mm
    estimates, then classifies overall density against CANVAS_H (275mm).
    """
    meta = payload.get("meta", {})
    subject = meta.get("subject", "math")
    if subject not in ("math", "english"):
        subject = "math"

    # --- feature flags ---
    pv = payload.get("page_visibility", {})
    has_city_compare = bool(pv.get("m5_city_compare", False))

    # composition: check composition_facts.feature_enabled OR m10.visible
    cf = payload.get("composition_facts", {})
    m10 = payload.get("m10", {})
    has_composition = bool(
        (isinstance(cf, dict) and cf.get("feature_enabled"))
        or (isinstance(m10, dict) and m10.get("visible"))
    )

    # reading_deep: check reading_deep_selection.feature_enabled OR m11.visible
    rds = payload.get("reading_deep_selection", {})
    m11 = payload.get("m11", {})
    has_reading_deep = bool(
        (isinstance(rds, dict) and rds.get("feature_enabled"))
        or (isinstance(m11, dict) and m11.get("visible"))
    )

    # --- counts ---
    domains_data = payload.get("domains", {})
    if isinstance(domains_data, dict):
        domain_items = domains_data.get("domain_items", domains_data.get("items", []))
    else:
        domain_items = []
    domain_count = len(domain_items) if isinstance(domain_items, list) else 0

    cw = payload.get("core_weakness", {})
    if isinstance(cw, dict):
        weakness_items = cw.get("items", [])
    else:
        weakness_items = []
    weakness_count = len(weakness_items) if isinstance(weakness_items, list) else 0
    has_weakness = weakness_count > 0

    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        total_kp = int(summary.get("high_freq_kp_total", 0) or 0)
    else:
        total_kp = 0

    # --- per-module volume estimates ---
    content_volume: dict[str, float] = {}
    for mod_id, estimator in _ESTIMATORS.items():
        blocks = estimator(payload)
        if blocks:
            content_volume[mod_id] = sum(h for _, h in blocks)

    # --- density ---
    total_mm = sum(content_volume.values())
    ratio = total_mm / CANVAS_H if CANVAS_H > 0 else 0.0

    if ratio < 0.4:
        density = "sparse"
    elif ratio <= 0.7:
        density = "normal"
    else:
        density = "dense"

    return DataProfile(
        subject=subject,
        density=density,
        content_volume=content_volume,
        has_weakness=has_weakness,
        has_city_compare=has_city_compare,
        has_composition=has_composition,
        has_reading_deep=has_reading_deep,
        domain_count=domain_count,
        weakness_count=weakness_count,
        total_kp=total_kp,
    )
