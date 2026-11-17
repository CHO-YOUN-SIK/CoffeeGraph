"""Phase 4 (M4): Full-dataset CQI Coffee Quality Analysis (1,339 records).

Analyzes arabica_data_cleaned.csv (1,311) + robusta_data_cleaned.csv (28) = 1,339 records:
- Missingness, duplicates, and score outliers (e.g., Total.Cup.Points == 0)
- Country of Origin & Processing Method distributions (sample bias diagnostics)
- Country & Processing Method score summaries with 95% confidence intervals
- Sensory variable correlation matrix
- Harvest year trends & OLS controlling for Country.of.Origin and Harvest.Year
- Verification of prior Natural vs Washed difference (~0.39 raw, ~0.27 country-adjusted)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
CQI_PATH = ROOT / "data" / "processed" / "cqi" / "cqi_combined.csv"
OUT_DIR = ROOT / "outputs" / "tables"

SENSORY_COLS = [
    "Aroma",
    "Flavor",
    "Aftertaste",
    "Acidity",
    "Body",
    "Balance",
    "Uniformity",
    "Clean.Cup",
    "Sweetness",
    "Cupper.Points",
    "Total.Cup.Points",
]


def ci95_mean(series: pd.Series) -> tuple[float, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = len(s)
    if n < 2:
        return float("nan"), float("nan")
    m = float(s.mean())
    se = float(s.std(ddof=1)) / np.sqrt(n)
    t_crit = float(stats.t.ppf(0.975, df=n - 1))
    return round(m - t_crit * se, 4), round(m + t_crit * se, 4)


def analyze_cqi_quality() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CQI_PATH)

    total_rows = len(df)
    dup_rows = int(df.duplicated().sum())
    outliers = df[pd.to_numeric(df["Total.Cup.Points"], errors="coerce") <= 0]

    # Valid Arabica subset (Total.Cup.Points > 0) for cupping score comparisons
    ar_all = df[df["Species_Source"] == "Arabica"].copy()
    ar = ar_all[pd.to_numeric(ar_all["Total.Cup.Points"], errors="coerce") > 0].copy()

    # Country summary (valid Arabica)
    country_rows = []
    for country, grp in ar.groupby("Country.of.Origin", dropna=False):
        lo, hi = ci95_mean(grp["Total.Cup.Points"])
        country_rows.append(
            {
                "Country.of.Origin": country if pd.notna(country) else "(Missing)",
                "count": int(len(grp)),
                "share_pct": round(len(grp) / len(ar) * 100, 2),
                "mean_cup_points": round(float(grp["Total.Cup.Points"].mean()), 4),
                "std_cup_points": round(float(grp["Total.Cup.Points"].std(ddof=1)), 4) if len(grp) > 1 else 0.0,
                "ci95_low": lo,
                "ci95_high": hi,
                "median_cup_points": round(float(grp["Total.Cup.Points"].median()), 4),
            }
        )
    country_df = pd.DataFrame(country_rows).sort_values("count", ascending=False).reset_index(drop=True)
    country_df.to_csv(OUT_DIR / "cqi_country_summary.csv", index=False, encoding="utf-8-sig")

    # Processing Method summary (valid Arabica)
    proc_rows = []
    for proc, grp in ar.groupby("Processing.Method", dropna=False):
        lo, hi = ci95_mean(grp["Total.Cup.Points"])
        proc_rows.append(
            {
                "Processing.Method": proc if pd.notna(proc) else "(Missing)",
                "count": int(len(grp)),
                "share_pct": round(len(grp) / len(ar) * 100, 2),
                "mean_cup_points": round(float(grp["Total.Cup.Points"].mean()), 4),
                "std_cup_points": round(float(grp["Total.Cup.Points"].std(ddof=1)), 4) if len(grp) > 1 else 0.0,
                "ci95_low": lo,
                "ci95_high": hi,
            }
        )
    proc_df = pd.DataFrame(proc_rows).sort_values("count", ascending=False).reset_index(drop=True)
    proc_df.to_csv(OUT_DIR / "cqi_processing_summary.csv", index=False, encoding="utf-8-sig")

    # Sensory correlation matrix (valid Arabica)
    corr_mat = ar[SENSORY_COLS].corr().round(4)
    corr_mat.to_csv(OUT_DIR / "cqi_sensory_correlations.csv", encoding="utf-8-sig")

    # Harvest year summary (clean 4-digit year where parseable)
    ar["Harvest_Year_Clean"] = ar["Harvest.Year"].astype(str).str.extract(r"(20\d{2}|19\d{2})")[0]
    harvest_df = (
        ar.dropna(subset=["Harvest_Year_Clean"])
        .groupby("Harvest_Year_Clean", as_index=False)["Total.Cup.Points"]
        .agg(count="count", mean="mean", std="std")
        .sort_values("Harvest_Year_Clean")
    )
    harvest_df["mean"] = harvest_df["mean"].round(4)
    harvest_df["std"] = harvest_df["std"].round(4)
    harvest_df.to_csv(OUT_DIR / "cqi_harvest_year_summary.csv", index=False, encoding="utf-8-sig")

    # Natural vs Washed comparison (raw + country-controlled + country & harvest-year-controlled)
    nw = ar[ar["Processing.Method"].isin(["Natural / Dry", "Washed / Wet"])].copy()
    nw["is_natural"] = (nw["Processing.Method"] == "Natural / Dry").astype(int)

    nat_pts = nw[nw["is_natural"] == 1]["Total.Cup.Points"]
    was_pts = nw[nw["is_natural"] == 0]["Total.Cup.Points"]
    t_stat, t_pval = stats.ttest_ind(nat_pts, was_pts, equal_var=False)
    raw_diff = float(nat_pts.mean() - was_pts.mean())

    nw_country = nw.dropna(subset=["Country.of.Origin"]).copy()
    m_country = smf.ols('Q("Total.Cup.Points") ~ is_natural + C(Q("Country.of.Origin"))', data=nw_country).fit()

    nw_full = nw_country.dropna(subset=["Harvest_Year_Clean"]).copy()
    m_full = smf.ols(
        'Q("Total.Cup.Points") ~ is_natural + C(Q("Country.of.Origin")) + C(Harvest_Year_Clean)',
        data=nw_full,
    ).fit()

    top5_countries_share = round(float(country_df.head(5)["share_pct"].sum()), 2)

    summary = {
        "total_records": int(total_rows),
        "species_counts": df["Species_Source"].value_counts().to_dict(),
        "duplicate_rows": dup_rows,
        "outlier_zero_or_negative_cup_points": int(len(outliers)),
        "valid_arabica_n": int(len(ar)),
        "top5_countries_share_pct": top5_countries_share,
        "natural_vs_washed": {
            "natural_n": int(len(nat_pts)),
            "washed_n": int(len(was_pts)),
            "natural_mean": round(float(nat_pts.mean()), 4),
            "washed_mean": round(float(was_pts.mean()), 4),
            "raw_diff": round(raw_diff, 4),
            "welch_t_stat": round(float(t_stat), 4),
            "welch_p_value": round(float(t_pval), 6),
            "country_adjusted_diff": round(float(m_country.params["is_natural"]), 4),
            "country_adjusted_p_value": round(float(m_country.pvalues["is_natural"]), 6),
            "country_adjusted_ci95": [
                round(float(x), 4) for x in m_country.conf_int().loc["is_natural"].tolist()
            ],
            "country_and_harvest_adjusted_n": int(len(nw_full)),
            "country_and_harvest_adjusted_diff": round(float(m_full.params["is_natural"]), 4),
            "country_and_harvest_adjusted_p_value": round(float(m_full.pvalues["is_natural"]), 6),
        },
        "missing_rates_top": {
            col: round(float(df[col].isna().mean()), 4)
            for col in ["Country.of.Origin", "Processing.Method", "Harvest.Year", "Altitude"]
            if col in df.columns
        },
    }

    (OUT_DIR / "cqi_regression_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    res = analyze_cqi_quality()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
