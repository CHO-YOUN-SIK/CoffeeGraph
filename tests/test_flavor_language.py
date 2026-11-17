"""Semantic & pipeline tests for Coffee Flavor Language Map.

Verifies not only output generation and statistical invariants, but also:
1. Word-boundary & non-overlapping lexical matching (no 배송->배, 중약배전->배, 모카포트->모카)
2. Zero website boilerplate contamination in raw brand descriptions
3. Product type & origin type classification (블렌드 != Single Origin, 세트/구독 != whole_bean)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.flavor_language import (
    analyze_flavor_language,
    classify_origin_type,
    classify_product_type,
    extract_sku_features,
)
from src.reporting.build_flavor_report import build_flavor_language_report
from src.visualization.flavor_language_map import (
    build_interactive_flavor_map,
    build_static_flavor_map,
)

ROOT = Path(__file__).resolve().parents[1]


def test_lexical_boundary_and_semantic_rules() -> None:
    # 1. '배송', '중약배전', '예배', '배운' must NEVER trigger Stone/Other Fruit ('배')
    f_false_pear = extract_sku_features(
        pd.Series({"sku_name": "테스트 원두", "description_raw": "중약배전 빠른 배송 예배 배운 맛", "tags_raw": ""})
    )
    assert f_false_pear["fam_Stone/Other Fruit_cnt"] == 0

    # Standalone '배' (pear) SHOULD match Stone/Other Fruit
    f_true_pear = extract_sku_features(
        pd.Series({"sku_name": "테스트 원두", "description_raw": "잘 익은 배, 복숭아의 단맛", "tags_raw": ""})
    )
    assert f_true_pear["fam_Stone/Other Fruit_cnt"] >= 2

    # 2. '모카포트' must NEVER trigger Chocolate/Cocoa ('모카')
    f_moka = extract_sku_features(
        pd.Series({"sku_name": "테스트 원두", "description_raw": "모카포트 추출 추천", "tags_raw": ""})
    )
    assert f_moka["fam_Chocolate/Cocoa_cnt"] == 0

    # 3. '다크초콜릿' should not double-count '초콜릿' on the same span
    f_choc = extract_sku_features(
        pd.Series({"sku_name": "테스트 원두", "description_raw": "진한 다크초콜릿 풍미", "tags_raw": ""})
    )
    assert f_choc["fam_Chocolate/Cocoa_cnt"] == 1

    # 4. Product type & origin type rules
    assert classify_product_type("윈터 블렌드 & 푸어 오버 키트 세트") == "set_kit"
    assert classify_product_type("커피리브레 커피홀릭 3개월 200g") == "subscription"
    assert classify_product_type("펠트 드립백 클래식 (30개입)") == "drip_bag"
    assert classify_origin_type("윈터 블렌드", "에티오피아 원두와 멕시코 원두의 조화") == "Blend"


def test_raw_data_free_of_site_boilerplate() -> None:
    raw = pd.read_csv(ROOT / "data" / "raw" / "brands" / "official_brand_beans_raw.csv")
    descs = raw["description_raw"].fillna("")
    for bad_phrase in ["추천 검색어", "피칸파이", "모카포트", "알림 뒤로", "배송 안내"]:
        assert int(descs.str.contains(bad_phrase).sum()) == 0, f"Boilerplate found: {bad_phrase}"


def test_flavor_language_pipeline() -> None:
    stats = analyze_flavor_language()
    assert stats["total_skus"] == 129
    assert stats["comparable_whole_bean_skus"] == 98
    assert stats["brand_count"] == 8

    for pop_key in ("all_skus", "whole_bean_only"):
        q1 = stats[pop_key]["q1_brand_vs_dominant_family"]
        assert q1["p_monte_carlo"] < 0.005
        assert q1["cramers_v"] > 0.3

        q2 = stats[pop_key]["q2_narrative_vs_specificity"]
        assert q2["ols_brand_fe_narrative_p"] > 0.05
        assert q2["ols_brand_fe_single_origin_p"] < 0.001

    html_path = build_interactive_flavor_map()
    png_path = build_static_flavor_map()
    assert html_path.exists() and html_path.stat().st_size > 10000
    assert png_path.exists() and png_path.stat().st_size > 20000

    report_path = build_flavor_language_report()
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Monte Carlo" in report_text
    assert "Multi-Family (Tie)" in report_text
    assert "whole_bean" in report_text
