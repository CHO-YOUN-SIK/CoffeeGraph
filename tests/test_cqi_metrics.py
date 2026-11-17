"""Tests for Phase 4 CQI full-dataset analysis metrics."""

from __future__ import annotations

from src.analysis.cqi_quality import analyze_cqi_quality


def test_cqi_full_dataset_and_natural_washed_diff() -> None:
    res = analyze_cqi_quality()
    assert res["total_records"] == 1339
    assert res["species_counts"] == {"Arabica": 1311, "Robusta": 28}
    assert res["outlier_zero_or_negative_cup_points"] == 1
    assert res["valid_arabica_n"] == 1310
    nw = res["natural_vs_washed"]
    assert abs(nw["raw_diff"] - 0.3895) < 0.02
    assert abs(nw["country_adjusted_diff"] - 0.2657) < 0.02
    assert nw["country_adjusted_p_value"] > 0.05
