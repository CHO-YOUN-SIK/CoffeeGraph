"""End-to-end pipeline tests for Phase 5-8 (Brand Positioning, Cross Analysis, Reports)."""

from __future__ import annotations

from pathlib import Path

from src.analysis.brand_positioning import analyze_brand_positioning
from src.analysis.cross_analysis import run_cross_analysis
from src.reporting.build_reports import generate_reports
from src.visualization.opportunity_map import build_opportunity_map

ROOT = Path(__file__).resolve().parents[1]


def test_brand_cross_and_reports_pipeline() -> None:
    b_res = analyze_brand_positioning()
    assert b_res["brand_count"] >= 7
    assert b_res["total_verified_skus"] >= 80

    c_res = run_cross_analysis()
    assert c_res["direct_join_districts"] == 25
    assert c_res["brand_context_count"] == b_res["brand_count"]

    html_path = build_opportunity_map()
    assert html_path.exists()
    assert html_path.stat().st_size > 10000

    paths = generate_reports()
    assert len(paths) == 5
    for p in paths:
        assert p.exists()
        assert p.stat().st_size > 200
