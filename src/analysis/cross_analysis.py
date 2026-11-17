"""Phase 6 (M6): Multi-Level Cross Analysis (Direct Join, Context Join, Comparative, Reference).

Strictly separates the 4 analytical join levels:
1. Direct Join: Seoul store + sales + consumer context on (기준_년분기_코드, 자치구_코드)
2. Context Join: Brand Seoul store districts linked to district/cluster market context
3. Comparative Analysis: Brand product & flavor communication across market contexts
4. Reference Analysis: CQI international cupping background vs domestic brand origin/process framing
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "outputs" / "tables"
PROCESSED_BRAND_DIR = ROOT / "data" / "processed" / "brands"


def run_cross_analysis() -> dict[str, Any]:
    # Level 1: Direct Join (25 districts, 20261)
    dist_sum = pd.read_csv(TABLES_DIR / "seoul_district_summary_20261.csv", dtype={"자치구_코드": str})
    dist_ctx = pd.read_csv(TABLES_DIR / "seoul_district_consumer_context_20261.csv", dtype={"자치구_코드": str})
    direct_df = dist_sum.merge(
        dist_ctx[
            [
                "자치구_코드",
                "시간_06~11_pct",
                "시간_11~14_pct",
                "시간_14~17_pct",
                "시간_17~21_pct",
                "연령대_20_pct",
                "연령대_30_pct",
                "연령대_40_pct",
            ]
        ],
        on="자치구_코드",
        how="inner",
    )
    direct_df.to_csv(TABLES_DIR / "cross_direct_district_20261.csv", index=False, encoding="utf-8-sig")

    # Classify districts by median split on sales_per_store & weekend_share for Context Join
    med_sps = direct_df["점포당_추정매출_억원"].median()
    med_wknd = direct_df["주말_매출_비중_pct"].median()

    # Level 2 & 3: Context Join + Comparative Analysis for Brands
    brand_sum = pd.read_csv(TABLES_DIR / "brand_positioning_summary.csv")
    context_rows = []
    for _, b in brand_sum.iterrows():
        d_list = [d.strip() for d in str(b["seoul_districts"]).split(",") if d.strip()]
        sub = direct_df[direct_df["자치구_코드_명"].isin(d_list)]
        context_rows.append(
            {
                "brand_id": b["brand_id"],
                "brand_name": b["brand_name"],
                "matched_seoul_districts": ",".join(d_list),
                "district_count": len(sub),
                "avg_district_sales_per_store_eok": round(float(sub["점포당_추정매출_억원"].mean()), 3) if not sub.empty else None,
                "avg_district_store_change_pct": round(float(sub["점포_증감률_pct"].mean()), 2) if not sub.empty else None,
                "avg_district_lunch_11_14_pct": round(float(sub["시간_11~14_pct"].mean()), 2) if not sub.empty else None,
                "avg_district_weekend_pct": round(float(sub["주말_매출_비중_pct"].mean()), 2) if not sub.empty else None,
                "sku_count": int(b["sku_count"]),
                "median_price_per_100g": b["median_price_per_100g"],
                "single_origin_share_pct": b["single_origin_share_pct"],
                "mean_sensory_dims": b["mean_sensory_dims"],
                "pct_감성적·추상적": b["pct_감성적·추상적"],
                "pct_과일": b["pct_과일"],
                "pct_산미": b["pct_산미"],
                "pct_초콜릿": b["pct_초콜릿"],
            }
        )
    ctx_df = pd.DataFrame(context_rows)
    ctx_df.to_csv(TABLES_DIR / "cross_brand_market_context.csv", index=False, encoding="utf-8-sig")

    # Level 4: Reference Analysis (CQI vs Brand Origin/Process)
    beans_coded = pd.read_csv(PROCESSED_BRAND_DIR / "official_brand_beans_coded.csv")
    cqi_reg = json.loads((TABLES_DIR / "cqi_regression_summary.json").read_text(encoding="utf-8"))
    cqi_country = pd.read_csv(TABLES_DIR / "cqi_country_summary.csv")

    brand_top_origins = (
        beans_coded["origins_detected"]
        .str.split(",")
        .explode()
        .value_counts()
        .head(8)
        .to_dict()
    )
    brand_process_counts = (
        beans_coded["process_detected"]
        .str.split(",")
        .explode()
        .value_counts()
        .to_dict()
    )

    summary = {
        "direct_join_districts": int(len(direct_df)),
        "median_sales_per_store_eok": round(float(med_sps), 4),
        "median_weekend_share_pct": round(float(med_wknd), 2),
        "brand_context_count": int(len(ctx_df)),
        "reference_cqi_vs_brands": {
            "cqi_natural_vs_washed_country_adj_diff": cqi_reg["natural_vs_washed"]["country_adjusted_diff"],
            "cqi_natural_vs_washed_country_adj_p": cqi_reg["natural_vs_washed"]["country_adjusted_p_value"],
            "cqi_top5_origins": cqi_country.head(5)["Country.of.Origin"].tolist(),
            "brand_top_origins": brand_top_origins,
            "brand_process_mentions": brand_process_counts,
        },
    }
    (TABLES_DIR / "cross_analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    res = run_cross_analysis()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
