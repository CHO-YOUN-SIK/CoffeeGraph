"""External Population Validation of Seoul Commercial Context Clusters (H-M1, H-M2, H-M3).

Validates the 4 consumer_context.py clusters (n=1,064 in 2026Q1) against
official Seoul Open Data commercial-area population tables:
- OA-15569 (Work Population) -> H-M1: 11-14h sales share vs work population
- OA-15584 (Resident Population) -> H-M2: 17-21h sales share vs resident population
- OA-15568 (Foot Traffic) -> H-M3: weekend sales share vs weekend foot traffic share

Also audits the 455 store-only commercial areas excluded from the 1,064 sales-matched
sample for selection bias.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_SEOUL_DIR = ROOT / "data" / "processed" / "seoul"
OUT_DIR = ROOT / "outputs" / "tables"


def run_market_external_validation() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clusters = pd.read_csv(OUT_DIR / "seoul_commercial_clusters_20261.csv")
    ctx = pd.read_csv(PROCESSED_SEOUL_DIR / "commercial_context_20261.csv")
    store_comm = pd.read_csv(PROCESSED_SEOUL_DIR / "cs100010_store_commercial.csv")
    s26 = store_comm[store_comm["기준_년분기_코드"].astype(str) == "20261"].copy()

    # Enforce join key uniqueness
    assert clusters["상권_코드"].is_unique
    assert ctx["상권_코드"].is_unique

    merged = clusters.merge(ctx, on="상권_코드", how="left")
    merged.to_csv(OUT_DIR / "seoul_commercial_validated_20261.csv", index=False, encoding="utf-8-sig")

    # Selection bias audit: 1,064 matched vs excluded store-only commercial areas
    matched_codes = set(clusters["상권_코드"])
    s26["is_matched_1064"] = s26["상권_코드"].isin(matched_codes)
    s26_ctx = s26.merge(ctx, on="상권_코드", how="left")
    incl = s26_ctx[s26_ctx["is_matched_1064"]]
    excl = s26_ctx[~s26_ctx["is_matched_1064"]]

    bias_audit = {}
    for col in ["전체_점포_수", "총_직장_인구_수", "총_유동인구_수", "총_상주인구_수"]:
        a = incl[col].dropna()
        b = excl[col].dropna()
        u_stat, p_u = stats.mannwhitneyu(a, b, alternative="two-sided") if len(a) and len(b) else (np.nan, np.nan)
        bias_audit[col] = {
            "included_n": int(len(a)),
            "included_median": round(float(a.median()), 1) if len(a) else None,
            "excluded_n": int(len(b)),
            "excluded_median": round(float(b.median()), 1) if len(b) else None,
            "mannwhitney_p": round(float(p_u), 6) if pd.notna(p_u) else None,
        }

    # H-M1: 11-14h sales share vs work population
    valid_w = merged.dropna(subset=["총_직장_인구_수", "시간_11~14_pct"]).copy()
    valid_w["log10_work"] = np.log10(1.0 + valid_w["총_직장_인구_수"].clip(lower=0))
    rho_hm1, p_rho_hm1 = stats.spearmanr(valid_w["총_직장_인구_수"], valid_w["시간_11~14_pct"])
    r_hm1, p_r_hm1 = stats.pearsonr(valid_w["log10_work"], valid_w["시간_11~14_pct"])
    kw_w_groups = [g["총_직장_인구_수"].dropna().values for _, g in merged.groupby("cluster_label")]
    kw_w_stat, kw_w_p = stats.kruskal(*kw_w_groups)

    # H-M2: 17-21h sales share vs resident population
    valid_r = merged.dropna(subset=["총_상주인구_수", "시간_17~21_pct"]).copy()
    valid_r["log10_res"] = np.log10(1.0 + valid_r["총_상주인구_수"].clip(lower=0))
    rho_hm2, p_rho_hm2 = stats.spearmanr(valid_r["총_상주인구_수"], valid_r["시간_17~21_pct"])
    r_hm2, p_r_hm2 = stats.pearsonr(valid_r["log10_res"], valid_r["시간_17~21_pct"])
    kw_r_groups = [g["총_상주인구_수"].dropna().values for _, g in merged.groupby("cluster_label")]
    kw_r_stat, kw_r_p = stats.kruskal(*kw_r_groups)

    # H-M3: Weekend sales share vs weekend foot traffic share
    valid_f = merged.dropna(subset=["주말_유동인구_비중", "주말_비중_pct"]).copy()
    rho_hm3, p_rho_hm3 = stats.spearmanr(valid_f["주말_유동인구_비중"], valid_f["주말_비중_pct"])
    r_hm3, p_r_hm3 = stats.pearsonr(valid_f["주말_유동인구_비중"], valid_f["주말_비중_pct"])

    # Cluster external profile summary
    prof = (
        merged.groupby("cluster_label")
        .agg(
            n_areas=("상권_코드", "count"),
            median_work_pop=("총_직장_인구_수", "median"),
            median_foot_pop=("총_유동인구_수", "median"),
            median_res_pop=("총_상주인구_수", "median"),
            mean_lunch_sales_pct=("시간_11~14_pct", "mean"),
            mean_evening_sales_pct=("시간_17~21_pct", "mean"),
            mean_weekend_sales_pct=("주말_비중_pct", "mean"),
            mean_weekend_foot_pct=("주말_유동인구_비중", "mean"),
        )
        .round(2)
        .reset_index()
    )
    prof.to_csv(OUT_DIR / "cluster_external_profile_20261.csv", index=False, encoding="utf-8-sig")

    # Label validity verdicts
    top_work_cluster = prof.sort_values("median_work_pop", ascending=False).iloc[0]["cluster_label"]
    top_res_cluster = prof.sort_values("median_res_pop", ascending=False).iloc[0]["cluster_label"]

    summary = {
        "matched_1064_coverage": {
            "work_pop_matched": int(merged["총_직장_인구_수"].notna().sum()),
            "foot_pop_matched": int(merged["총_유동인구_수"].notna().sum()),
            "res_pop_matched": int(merged["총_상주인구_수"].notna().sum()),
        },
        "selection_bias_455_excluded": bias_audit,
        "h_m1_office_lunch_vs_work_pop": {
            "n": int(len(valid_w)),
            "spearman_rho": round(float(rho_hm1), 4),
            "spearman_p": round(float(p_rho_hm1), 6),
            "pearson_r_log10": round(float(r_hm1), 4),
            "pearson_p": round(float(p_r_hm1), 6),
            "cluster_kruskal_h": round(float(kw_w_stat), 3),
            "cluster_kruskal_p": round(float(kw_w_p), 6),
            "highest_median_work_pop_cluster": str(top_work_cluster),
        },
        "h_m2_evening_life_vs_resident_pop": {
            "n": int(len(valid_r)),
            "spearman_rho": round(float(rho_hm2), 4),
            "spearman_p": round(float(p_rho_hm2), 6),
            "pearson_r_log10": round(float(r_hm2), 4),
            "pearson_p": round(float(p_r_hm2), 6),
            "cluster_kruskal_h": round(float(kw_r_stat), 3),
            "cluster_kruskal_p": round(float(kw_r_p), 6),
            "highest_median_res_pop_cluster": str(top_res_cluster),
        },
        "h_m3_weekend_sales_vs_foot_traffic": {
            "n": int(len(valid_f)),
            "spearman_rho": round(float(rho_hm3), 4),
            "spearman_p": round(float(p_rho_hm3), 6),
            "pearson_r": round(float(r_hm3), 4),
            "pearson_p": round(float(p_r_hm3), 6),
        },
        "cluster_external_profiles": prof.to_dict(orient="records"),
    }
    (OUT_DIR / "market_external_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    res = run_market_external_validation()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
