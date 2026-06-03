"""Adapter registry for payload normalization.

Protocol:
    detect(payload) -> bool
    adapt(payload) -> dict

Usage:
    from adapters import adapt_payload
    normalized = adapt_payload(raw_payload)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PayloadAdapter(Protocol):
    def detect(self, payload: dict) -> bool: ...
    def adapt(self, payload: dict) -> dict: ...


_ADAPTERS: list[PayloadAdapter] = []


def register(adapter: PayloadAdapter) -> None:
    """Register an adapter instance."""
    _ADAPTERS.append(adapter)


def adapt_payload(payload: dict) -> dict:
    """Run the first matching adapter, or return payload with defaults."""
    for adapter in _ADAPTERS:
        if adapter.detect(payload):
            return adapter.adapt(payload)
    return _ensure_page_visibility(payload)


def _ensure_page_visibility(payload: dict) -> dict:
    """Add missing page_visibility defaults for standard (non-brief) payloads."""
    if "page_visibility" not in payload:
        payload["page_visibility"] = {}
    pv = payload["page_visibility"]
    pv.setdefault("m5_city_compare", True)
    pv.setdefault("m10_composition", False)
    pv.setdefault("m11_reading_deep", False)
    pv.setdefault("show_teacher_supplement", False)
    return payload


# --- Auto-register built-in adapters ---
from adapters.english_brief import EnglishBriefAdapter  # noqa: E402

register(EnglishBriefAdapter())
