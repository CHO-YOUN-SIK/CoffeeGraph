"""Tests for Track A (WCR Lexicon Mapping, Center Coffee Audit, TOST)
and Track B (Seoul External Population Validation H-M1/H-M2/H-M3 & Visualization C).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.flavor_language import analyze_flavor_language
from src.analysis.lexicon_validation import (
    audit_center_coffee_zero_detection,
    export_wcr_lexicon_mapping,
)
from src.analysis.market_external_validation import run_market_external_validation
from src.visualization.market_validation_map import build_market_validation_maps

ROOT = Path(__file__).resolve().parents[1]


def test_wcr_lexicon_mapping_and_tost_equivalence() -> None:
    mapping_path = export_wcr_lexicon_mapping()
    assert mapping_path.exists()
    mdf = pd.read_csv(mapping_path)
    assert set(mdf["flavor_family"].unique()) == {
        "Berry",
        "Citrus",
        "Stone/Other Fruit",
        "Floral",
        "Nutty",
        "Chocolate/Cocoa",
        "Sweet/Caramel",
    }
    assert "wcr_reference_category" in mdf.columns

    cc_audit = audit_center_coffee_zero_detection()
    assert cc_audit["sku_count"] == 7

    stats = analyze_flavor_language()
    q2_all = stats["all_skus"]["q2_narrative_vs_specificity"]
    assert len(q2_all["ols_brand_fe_narrative_ci95"]) == 2
    assert q2_all["ols_brand_fe_narrative_tost_p"] < 0.05


def test_seoul_external_population_validation_and_visual_c() -> None:
    ctx_path = ROOT / "data" / "processed" / "seoul" / "commercial_context_20261.csv"
    assert ctx_path.exists()
    ctx = pd.read_csv(ctx_path)
    assert ctx["상권_코드"].is_unique

    res = run_market_external_validation()
    assert res["matched_1064_coverage"]["work_pop_matched"] >= 1050
    assert res["h_m1_office_lunch_vs_work_pop"]["highest_median_work_pop_cluster"] == "오피스·점심 집중형"
    assert res["h_m1_office_lunch_vs_work_pop"]["cluster_kruskal_p"] < 0.001
    assert res["h_m3_weekend_sales_vs_foot_traffic"]["spearman_rho"] > 0.4
    assert res["selection_bias_455_excluded"]["전체_점포_수"]["excluded_n"] == 455

    png_path, html_path = build_market_validation_maps()
    assert png_path.exists() and png_path.stat().st_size > 20000
    assert html_path.exists() and html_path.stat().st_size > 10000
