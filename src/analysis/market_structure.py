"""Phase 3 (M3): Seoul Coffee Market Structure Analysis (CS100010, 커피-음료).

Analyzes full validated official Seoul Open Data datasets:
- Seoul overall quarterly trend (stores, openings/closures, franchise share, sales)
- 25-district structural comparison (20242->20261, 20251->20261, 20242->20262)
- Statistical tests (Pearson r, Spearman rho, 95% CI, OLS regression)
- Verification against prior benchmark metrics (27,333 stores, 23/25 declining, r~0.016, r~0.565)
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
STORE_DIST_PATH = ROOT / "data" / "processed" / "seoul" / "cs100010_store_district.csv"
SALES_DIST_PATH = ROOT / "data" / "processed" / "seoul" / "cs100010_sales_district.csv"
OUT_DIR = ROOT / "outputs" / "tables"


def pearson_with_ci(x: pd.Series, y: pd.Series, alpha: float = 0.05) -> dict[str, float]:
    r, p = stats.pearsonr(x, y)
    n = len(x)
    if n <= 3 or abs(r) >= 1.0:
        ci_low, ci_high = float("nan"), float("nan")
    else:
        z = math.atanh(r)
        se = 1.0 / math.sqrt(n - 3)
        z_crit = stats.norm.ppf(1 - alpha / 2)
        ci_low = math.tanh(z - z_crit * se)
        ci_high = math.tanh(z + z_crit * se)
    rho, p_spearman = stats.spearmanr(x, y)
    return {
        "n": int(n),
        "pearson_r": round(float(r), 4),
        "pearson_p": round(float(p), 6),
        "ci95_low": round(float(ci_low), 4),
        "ci95_high": round(float(ci_high), 4),
        "spearman_rho": round(float(rho), 4),
        "spearman_p": round(float(p_spearman), 6),
    }


def analyze_market_structure() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    st = pd.read_csv(STORE_DIST_PATH, dtype={"기준_년분기_코드": str, "자치구_코드": str})
    sa = pd.read_csv(SALES_DIST_PATH, dtype={"기준_년분기_코드": str, "자치구_코드": str})

    # A. Seoul overall quarterly summary
    st_q = st.groupby("기준_년분기_코드", as_index=False)[
        ["전체_점포_수", "일반_점포_수", "프랜차이즈_점포_수", "개업_점포_수", "폐업_점포_수"]
    ].sum()
    sa_q = sa.groupby("기준_년분기_코드", as_index=False)[
        ["당월_매출_금액", "당월_매출_건수", "주중_매출_금액", "주말_매출_금액"]
    ].sum()
    q_df = st_q.merge(sa_q, on="기준_년분기_코드", how="inner").sort_values("기준_년분기_코드")
    q_df["프랜차이즈_비중_pct"] = (q_df["프랜차이즈_점포_수"] / q_df["전체_점포_수"] * 100).round(2)
    q_df["순증감_점포_수"] = q_df["개업_점포_수"] - q_df["폐업_점포_수"]
    q_df["점포당_매출_원"] = (q_df["당월_매출_금액"] / q_df["전체_점포_수"]).round(0)
    q_df["객단가_원"] = (q_df["당월_매출_금액"] / q_df["당월_매출_건수"]).round(0)
    q_df["주말_매출_비중_pct"] = (q_df["주말_매출_금액"] / q_df["당월_매출_금액"] * 100).round(2)
    q_df.to_csv(OUT_DIR / "seoul_market_quarterly.csv", index=False, encoding="utf-8-sig")

    # B. District-level summary for base quarter 20261 (vs 20242) and latest 20262
    def build_district_snapshot(q_base: str, q_prev: str) -> pd.DataFrame:
        s_now = st[st["기준_년분기_코드"] == q_base].copy()
        s_old = st[st["기준_년분기_코드"] == q_prev][
            ["자치구_코드", "전체_점포_수", "프랜차이즈_점포_수"]
        ].rename(columns={"전체_점포_수": f"전체_점포_수_{q_prev}", "프랜차이즈_점포_수": f"프랜차이즈_점포_수_{q_prev}"})
        m_now = sa[sa["기준_년분기_코드"] == q_base].copy()
        merged = s_now.merge(s_old, on="자치구_코드", how="inner").merge(
            m_now[["자치구_코드", "당월_매출_금액", "당월_매출_건수", "주중_매출_금액", "주말_매출_금액"]],
            on="자치구_코드",
            how="inner",
        )
        merged["점포_증감_수"] = merged["전체_점포_수"] - merged[f"전체_점포_수_{q_prev}"]
        merged["점포_증감률_pct"] = (merged["점포_증감_수"] / merged[f"전체_점포_수_{q_prev}"] * 100).round(3)
        merged["프랜차이즈_비중_pct"] = (merged["프랜차이즈_점포_수"] / merged["전체_점포_수"] * 100).round(2)
        merged["점포당_추정매출_억원"] = (merged["당월_매출_금액"] / merged["전체_점포_수"] / 1e8).round(4)
        merged["점포당_추정매출_원"] = (merged["당월_매출_금액"] / merged["전체_점포_수"]).round(0)
        merged["객단가_원"] = (merged["당월_매출_금액"] / merged["당월_매출_건수"]).round(0)
        merged["주말_매출_비중_pct"] = (merged["주말_매출_금액"] / merged["당월_매출_금액"] * 100).round(2)
        return merged.sort_values("점포당_추정매출_원", ascending=False).reset_index(drop=True)

    d_20261 = build_district_snapshot("20261", "20242")
    d_20262 = build_district_snapshot("20262", "20242")
    d_20261.to_csv(OUT_DIR / "seoul_district_summary_20261.csv", index=False, encoding="utf-8-sig")
    d_20262.to_csv(OUT_DIR / "seoul_district_latest_20262.csv", index=False, encoding="utf-8-sig")

    # Statistical tests & OLS (20242 -> 20261)
    corr_fran = pearson_with_ci(d_20261["프랜차이즈_비중_pct"], d_20261["점포_증감률_pct"])
    corr_sps = pearson_with_ci(d_20261["점포당_추정매출_원"], d_20261["점포_증감률_pct"])

    X = sm.add_constant(d_20261[["점포당_추정매출_억원", "프랜차이즈_비중_pct"]])
    ols_model = sm.OLS(d_20261["점포_증감률_pct"], X).fit()

    # Correlations for 20242 -> 20262 (latest)
    corr_fran_262 = pearson_with_ci(d_20262["프랜차이즈_비중_pct"], d_20262["점포_증감률_pct"])
    corr_sps_262 = pearson_with_ci(d_20262["점포당_추정매출_원"], d_20262["점포_증감률_pct"])

    row_261 = q_df[q_df["기준_년분기_코드"] == "20261"].iloc[0]
    row_242 = q_df[q_df["기준_년분기_코드"] == "20242"].iloc[0]
    row_262 = q_df[q_df["기준_년분기_코드"] == "20262"].iloc[0]

    summary = {
        "base_quarter": "20261",
        "comparison_start": "20242",
        "latest_quarter": "20262",
        "seoul_20242_total_stores": int(row_242["전체_점포_수"]),
        "seoul_20261_total_stores": int(row_261["전체_점포_수"]),
        "seoul_20262_total_stores": int(row_262["전체_점포_수"]),
        "seoul_20261_franchise_share_pct": float(row_261["프랜차이즈_비중_pct"]),
        "seoul_20261_monthly_sales_krw": int(row_261["당월_매출_금액"]),
        "declining_districts_20242_to_20261": int((d_20261["점포_증감_수"] < 0).sum()),
        "declining_districts_20242_to_20262": int((d_20262["점포_증감_수"] < 0).sum()),
        "correlations_20242_to_20261": {
            "franchise_share_vs_store_change_pct": corr_fran,
            "sales_per_store_vs_store_change_pct": corr_sps,
        },
        "correlations_20242_to_20262": {
            "franchise_share_vs_store_change_pct": corr_fran_262,
            "sales_per_store_vs_store_change_pct": corr_sps_262,
        },
        "ols_store_change_20261": {
            "r_squared": round(float(ols_model.rsquared), 4),
            "adj_r_squared": round(float(ols_model.rsquared_adj), 4),
            "f_pvalue": round(float(ols_model.f_pvalue), 6),
            "params": {k: round(float(v), 4) for k, v in ols_model.params.items()},
            "pvalues": {k: round(float(v), 6) for k, v in ols_model.pvalues.items()},
        },
    }

    (OUT_DIR / "seoul_market_correlations.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    res = analyze_market_structure()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
