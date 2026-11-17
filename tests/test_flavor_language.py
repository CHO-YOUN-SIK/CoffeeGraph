"""Tests for refactored Coffee Flavor Language Map analysis, visualization, and reporting."""

from __future__ import annotations

from pathlib import Path

from src.analysis.flavor_language import analyze_flavor_language
from src.reporting.build_flavor_report import build_flavor_language_report
from src.visualization.flavor_language_map import (
    build_interactive_flavor_map,
    build_static_flavor_map,
)

ROOT = Path(__file__).resolve().parents[1]


def test_flavor_language_pipeline() -> None:
    stats = analyze_flavor_language()
    assert stats["total_skus"] == 129
    assert stats["brand_count"] == 8
    assert stats["specificity_tier_counts"]["Specific-Anchored"] == 75
    assert stats["specificity_tier_counts"]["Broad-Only"] == 11
    assert stats["specificity_tier_counts"]["None-Stated"] == 43

    q1 = stats["q1_brand_vs_dominant_family"]
    assert q1["p_value"] < 0.001
    assert q1["cramers_v"] > 0.4

    q2 = stats["q2_narrative_vs_specificity"]
    assert q2["ols_controlled_r2"] > 0.15
    assert q2["ols_narrative_p"] > 0.05
    assert q2["ols_single_origin_p"] < 0.001
    assert q2["ols_single_origin_coef"] > 3.0

    html_path = build_interactive_flavor_map()
    png_path = build_static_flavor_map()
    assert html_path.exists() and html_path.stat().st_size > 10000
    assert png_path.exists() and png_path.stat().st_size > 20000

    report_path = build_flavor_language_report()
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "129개 원두 SKU" in report_text
    assert "0.4405" in report_text
    assert "is_single_origin" in report_text
    assert "색–향미" in report_text
