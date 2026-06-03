"""Tests for data_profile.py -- compute_data_profile()"""
import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from golden_typeset.data_profile import compute_data_profile, DataProfile


def _math_payload() -> dict:
    """Minimal math payload with realistic structure."""
    return {
        "meta": {"subject": "math"},
        "summary": {
            "high_freq_kp_total": 14,
            "current_accuracy": 72.0,
        },
        "domains": {
            "domain_items": [
                {"name_cn": "algebra"},
                {"name_cn": "geometry"},
                {"name_cn": "statistics"},
                {"name_cn": "functions"},
            ],
        },
        "core_weakness": {
            "items": [
                {"name_cn": "weak1"},
                {"name_cn": "weak2"},
                {"name_cn": "weak3"},
            ],
        },
        "page_visibility": {
            "m5_city_compare": True,
            "m10_composition": False,
            "m11_reading_deep": False,
        },
        "key_findings": ["finding1", "finding2"],
        "breakthrough": {"items": []},
        "suggestion": {"text": "study more"},
        "kp_drill": {"domains": []},
        "city_compare": {"overlap_items": [], "advice": []},
        "data_reliability": {},
        "question_detail": {"papers": []},
    }


def _english_payload() -> dict:
    """Minimal english payload with realistic structure."""
    return {
        "meta": {"subject": "english"},
        "summary": {
            "high_freq_kp_total": 8,
            "current_accuracy": 85.0,
        },
        "domains": {
            "domain_items": [
                {"name_cn": "vocabulary"},
                {"name_cn": "grammar"},
                {"name_cn": "reading"},
            ],
        },
        "core_weakness": {
            "items": [],
        },
        "page_visibility": {
            "m5_city_compare": False,
            "m10_composition": True,
            "m11_reading_deep": True,
        },
        "composition_facts": {"feature_enabled": True},
        "reading_deep_selection": {"feature_enabled": True},
        "key_findings": [],
        "breakthrough": {"items": []},
        "suggestion": {"text": ""},
        "kp_drill": {"domains": []},
        "city_compare": {"overlap_items": [], "advice": []},
        "data_reliability": {},
        "question_detail": {"papers": []},
    }


def test_compute_data_profile_math():
    """Math payload should produce correct DataProfile."""
    payload = _math_payload()
    dp = compute_data_profile(payload)

    assert isinstance(dp, DataProfile)
    assert dp.subject == "math"
    assert dp.has_city_compare is True
    assert dp.has_composition is False
    assert dp.has_reading_deep is False
    assert dp.has_weakness is True
    assert dp.domain_count == 4
    assert dp.weakness_count == 3
    assert dp.total_kp == 14
    assert isinstance(dp.content_volume, dict)
    # Should have some estimated modules
    assert len(dp.content_volume) > 0


def test_compute_data_profile_english():
    """English payload should detect composition and reading_deep features."""
    payload = _english_payload()
    dp = compute_data_profile(payload)

    assert isinstance(dp, DataProfile)
    assert dp.subject == "english"
    assert dp.has_city_compare is False
    assert dp.has_composition is True
    assert dp.has_reading_deep is True
    assert dp.has_weakness is False
    assert dp.domain_count == 3
    assert dp.weakness_count == 0
    assert dp.total_kp == 8


def test_density_classification():
    """Density should classify correctly based on total content volume."""
    # Math payload with minimal data -> likely sparse or normal
    payload = _math_payload()
    dp = compute_data_profile(payload)
    assert dp.density in ("sparse", "normal", "dense")

    # Heavy payload with many items -> dense
    heavy = _math_payload()
    heavy["core_weakness"]["items"] = [{"name_cn": f"weak{i}"} for i in range(20)]
    heavy["key_findings"] = [f"finding with lots of text content {i}" for i in range(20)]
    heavy["kp_drill"]["domains"] = [
        {
            "l2_items": [{"name": f"kp{j}"} for j in range(10)],
            "l3_items": [{"name": f"kp{j}"} for j in range(10)],
            "l4_items": [{"name": f"kp{j}"} for j in range(10)],
        }
        for i in range(6)
    ]
    dp_heavy = compute_data_profile(heavy)
    assert dp_heavy.density in ("dense", "normal")


def test_content_volume_has_expected_modules():
    """content_volume should include estimates for modules with data."""
    payload = _math_payload()
    dp = compute_data_profile(payload)
    # Math payload has domain items, core weakness, etc.
    # At minimum m1, m2, m4 should have estimates
    assert "m1" in dp.content_volume
    assert "m2" in dp.content_volume
    assert "m4" in dp.content_volume


def test_defaults_when_missing_fields():
    """Profile should handle payloads with missing optional fields."""
    minimal = {
        "meta": {"subject": "math"},
    }
    dp = compute_data_profile(minimal)
    assert dp.subject == "math"
    assert dp.domain_count == 0
    assert dp.weakness_count == 0
    assert dp.has_weakness is False
    assert dp.has_city_compare is False
    assert dp.has_composition is False
    assert dp.has_reading_deep is False
    assert dp.total_kp == 0


def test_m10_m11_visible_flag():
    """composition and reading_deep should be detected from m10/m11 visible."""
    payload = _math_payload()
    payload["m10"] = {"visible": True}
    payload["m11"] = {"visible": True}
    dp = compute_data_profile(payload)
    assert dp.has_composition is True
    assert dp.has_reading_deep is True


if __name__ == "__main__":
    test_compute_data_profile_math()
    test_compute_data_profile_english()
    test_density_classification()
    test_content_volume_has_expected_modules()
    test_defaults_when_missing_fields()
    test_m10_m11_visible_flag()
    print("All data_profile tests passed.")
