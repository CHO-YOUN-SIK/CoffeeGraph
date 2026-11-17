"""Tests for Phase 3 Seoul market structure & consumer context metrics."""

from __future__ import annotations

from src.analysis.consumer_context import analyze_consumer_context
from src.analysis.market_structure import analyze_market_structure


def test_seoul_market_metrics_reproducible() -> None:
    res = analyze_market_structure()
    assert res["seoul_20261_total_stores"] == 27333
    assert res["declining_districts_20242_to_20261"] == 23
    corr = res["correlations_20242_to_20261"]
    assert abs(corr["franchise_share_vs_store_change_pct"]["pearson_r"] - 0.0145) < 0.01
    assert abs(corr["sales_per_store_vs_store_change_pct"]["pearson_r"] - 0.5641) < 0.01
    assert corr["sales_per_store_vs_store_change_pct"]["pearson_p"] < 0.01


def test_consumer_context_clusters_20261() -> None:
    res = analyze_consumer_context(base_quarter="20261", n_clusters=4)
    assert res["district_count"] == 25
    assert res["commercial_area_count"] > 1000
    assert len(res["cluster_summary"]) == 4
