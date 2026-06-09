"""Adapter registry for payload normalization.

Protocol:
    detect(payload) -> bool
    adapt(payload) -> dict

Usage:
    from adapters import adapt_payload
    normalized = adapt_payload(raw_payload)
"""

from __future__ import annotations

import re as _re
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
            return _normalize_student_display_name(adapter.adapt(payload))
    return _normalize_student_display_name(_ensure_page_visibility(payload))


_MACHINE_STUDENT_RE = _re.compile(
    r"^([A-Za-z]+\d+)-(?:MATH|MATHEMATICS|ENG|ENGLISH)-\d{8}_\d{6}$",
    _re.IGNORECASE,
)

_CJK_RE = _re.compile(r"[\u4e00-\u9fff]")


def _normalize_student_display_name(payload: dict) -> dict:
    """Clean machine-generated student names (e.g. WO6-MATH-20260531_192939 → W O 6)."""
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return payload

    raw_name = meta.get("student_display_name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return payload

    # Chinese names / sample names: keep as-is
    if _CJK_RE.search(raw_name):
        return payload

    m = _MACHINE_STUDENT_RE.match(raw_name.strip())
    if not m:
        return payload

    code = m.group(1)
    clean_name = " ".join(code)  # "WO6" → "W O 6"
    if clean_name == raw_name:
        return payload

    # Global replacement across all payload string values
    _replace_all_strings(payload, raw_name, clean_name)
    meta["student_display_name"] = clean_name

    cover = payload.get("cover")
    if isinstance(cover, dict):
        cm = cover.get("cover_meta")
        if isinstance(cm, dict):
            cm["student_name"] = clean_name

    return payload


def _replace_all_strings(obj, old: str, new: str):
    """Recursively replace old with new in all string values (in-place).

    old is the full machine-code student name (e.g. WO6-MATH-20260531_192939),
    a unique token that will not substring-match unrelated content, so
    str.replace is safe and also covers composite fields like page_title.
    """
    if old == new:
        return
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            val = obj[key]
            if isinstance(val, str) and old in val:
                obj[key] = val.replace(old, new)
            else:
                _replace_all_strings(val, old, new)
    elif isinstance(obj, list):
        for i in range(len(obj)):
            val = obj[i]
            if isinstance(val, str) and old in val:
                obj[i] = val.replace(old, new)
            else:
                _replace_all_strings(val, old, new)


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
