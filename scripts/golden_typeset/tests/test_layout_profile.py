"""Tests for layout_profile.py -- compute_layout_profile()"""
import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from golden_typeset.data_profile import DataProfile
from golden_typeset.layout_profile import (
    compute_layout_profile,
    LayoutProfile,
)


def _make_profile(subject="math", density="normal", **kwargs) -> DataProfile:
    """Helper to build a DataProfile with defaults."""
    defaults = dict(
        subject=subject,
        density=density,
        content_volume={},
        has_weakness=False,
        has_city_compare=False,
        has_composition=False,
        has_reading_deep=False,
        domain_count=0,
        weakness_count=0,
        total_kp=0,
    )
    defaults.update(kwargs)
    return DataProfile(**defaults)


def test_layout_profile_math_dense():
    """math+dense should map to compact profile."""
    dp = _make_profile(subject="math", density="dense")
    lp = compute_layout_profile(dp)
    assert isinstance(lp, LayoutProfile)
    assert lp.spacing_mode == "compact"
    assert lp.typography_scale == 0.85
    assert lp.padding_scale == 0.60
    assert lp.grid_columns == 1
    assert lp.page_strategy == "single"


def test_layout_profile_math_normal():
    """math+normal should map to golden profile."""
    dp = _make_profile(subject="math", density="normal")
    lp = compute_layout_profile(dp)
    assert lp.spacing_mode == "golden"
    assert lp.typography_scale == 0.92
    assert lp.padding_scale == 0.80
    assert lp.grid_columns == 1
    assert lp.page_strategy == "single"


def test_layout_profile_math_sparse():
    """math+sparse should map to spacious profile."""
    dp = _make_profile(subject="math", density="sparse")
    lp = compute_layout_profile(dp)
    assert lp.spacing_mode == "spacious"
    assert lp.typography_scale == 1.00
    assert lp.padding_scale == 1.00
    assert lp.grid_columns == 1


def test_layout_profile_english_dense():
    """english+dense should map to compact with 2 columns and flow strategy."""
    dp = _make_profile(subject="english", density="dense")
    lp = compute_layout_profile(dp)
    assert lp.spacing_mode == "compact"
    assert lp.typography_scale == 0.85
    assert lp.padding_scale == 0.65
    assert lp.grid_columns == 2
    assert lp.page_strategy == "flow"


def test_layout_profile_english_normal():
    """english+normal should map to golden with 2 columns."""
    dp = _make_profile(subject="english", density="normal")
    lp = compute_layout_profile(dp)
    assert lp.spacing_mode == "golden"
    assert lp.grid_columns == 2
    assert lp.page_strategy == "single"


def test_layout_profile_english_sparse():
    """english+sparse should map to spacious with 2 columns."""
    dp = _make_profile(subject="english", density="sparse")
    lp = compute_layout_profile(dp)
    assert lp.spacing_mode == "spacious"
    assert lp.grid_columns == 2


def test_module_override_m3():
    """m3 should get module-specific override regardless of base profile."""
    dp = _make_profile(subject="math", density="normal")
    lp = compute_layout_profile(dp, mod_id="m3")
    assert lp.spacing_mode == "compact"
    assert lp.typography_scale == 0.82
    assert lp.padding_scale == 0.55
    assert lp.grid_columns == 2
    assert lp.page_strategy == "natural"


def test_module_override_m9():
    """m9 should get module-specific override."""
    dp = _make_profile(subject="math", density="normal")
    lp = compute_layout_profile(dp, mod_id="m9")
    assert lp.spacing_mode == "compact"
    assert lp.typography_scale == 0.80
    assert lp.padding_scale == 0.50
    assert lp.grid_columns == 1
    assert lp.page_strategy == "natural"


def test_no_module_override_for_general():
    """Non-overridden modules should use base profile."""
    dp = _make_profile(subject="math", density="normal")
    lp = compute_layout_profile(dp, mod_id="m1")
    assert lp.spacing_mode == "golden"  # from math+normal base


def test_css_overrides_present():
    """css_overrides should contain expected CSS variables."""
    dp = _make_profile(subject="math", density="dense")
    lp = compute_layout_profile(dp)
    assert isinstance(lp.css_overrides, dict)
    assert "--typography-scale" in lp.css_overrides
    assert "--padding-scale" in lp.css_overrides
    assert "--module-padding" in lp.css_overrides
    assert "--section-gap" in lp.css_overrides
    assert "--card-padding" in lp.css_overrides
    assert "--table-row-height" in lp.css_overrides
    assert "--grid-gap" in lp.css_overrides


def test_css_overrides_values_compact():
    """Compact mode should produce smaller CSS values."""
    dp = _make_profile(subject="math", density="dense")
    lp = compute_layout_profile(dp)
    assert lp.css_overrides["--section-gap"] == "8px"
    assert lp.css_overrides["--table-row-height"] == "6.5mm"


def test_css_overrides_values_spacious():
    """Spacious mode should produce larger CSS values."""
    dp = _make_profile(subject="math", density="sparse")
    lp = compute_layout_profile(dp)
    assert lp.css_overrides["--section-gap"] == "16px"
    assert lp.css_overrides["--table-row-height"] == "8.0mm"


def test_typography_scale_range():
    """typography_scale should be within 0.80 - 1.00."""
    for subject in ("math", "english"):
        for density in ("sparse", "normal", "dense"):
            dp = _make_profile(subject=subject, density=density)
            lp = compute_layout_profile(dp)
            assert 0.80 <= lp.typography_scale <= 1.00, (
                f"typography_scale={lp.typography_scale} out of range "
                f"for {subject}/{density}"
            )


def test_padding_scale_range():
    """padding_scale should be within 0.50 - 1.00."""
    for subject in ("math", "english"):
        for density in ("sparse", "normal", "dense"):
            dp = _make_profile(subject=subject, density=density)
            lp = compute_layout_profile(dp)
            assert 0.50 <= lp.padding_scale <= 1.00, (
                f"padding_scale={lp.padding_scale} out of range "
                f"for {subject}/{density}"
            )


def test_grid_gap_range():
    """grid_gap_mm should be within 3.0 - 8.0."""
    for subject in ("math", "english"):
        for density in ("sparse", "normal", "dense"):
            dp = _make_profile(subject=subject, density=density)
            lp = compute_layout_profile(dp)
            assert 3.0 <= lp.grid_gap_mm <= 8.0, (
                f"grid_gap_mm={lp.grid_gap_mm} out of range "
                f"for {subject}/{density}"
            )


if __name__ == "__main__":
    test_layout_profile_math_dense()
    test_layout_profile_math_normal()
    test_layout_profile_math_sparse()
    test_layout_profile_english_dense()
    test_layout_profile_english_normal()
    test_layout_profile_english_sparse()
    test_module_override_m3()
    test_module_override_m9()
    test_no_module_override_for_general()
    test_css_overrides_present()
    test_css_overrides_values_compact()
    test_css_overrides_values_spacious()
    test_typography_scale_range()
    test_padding_scale_range()
    test_grid_gap_range()
    print("All layout_profile tests passed.")
