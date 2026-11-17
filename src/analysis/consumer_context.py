"""Phase 3 (M3): Seoul Consumer Context Analysis (Time-slot, Day-of-Week, Age, Commercial Clusters).

Analyzes district-level and commercial-area-level (상권) consumer context for
CS100010 (커피-음료) in base quarter 20261, and performs standardized KMeans
clustering on commercial areas to empirically identify market context archetypes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
SALES_DIST_PATH = ROOT / "data" / "processed" / "seoul" / "cs100010_sales_district.csv"
STORE_COMM_PATH = ROOT / "data" / "processed" / "seoul" / "cs100010_store_commercial.csv"
SALES_COMM_PATH = ROOT / "data" / "processed" / "seoul" / "cs100010_sales_commercial.csv"
OUT_DIR = ROOT / "outputs" / "tables"

TIME_COLS = [
    "시간대_00~06_매출_금액",
    "시간대_06~11_매출_금액",
    "시간대_11~14_매출_금액",
    "시간대_14~17_매출_금액",
    "시간대_17~21_매출_금액",
    "시간대_21~24_매출_금액",
]
AGE_COLS = [
    "연령대_10_매출_금액",
    "연령대_20_매출_금액",
    "연령대_30_매출_금액",
    "연령대_40_매출_금액",
    "연령대_50_매출_금액",
    "연령대_60_이상_매출_금액",
]


def add_context_shares(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    total = out["당월_매출_금액"].replace(0, np.nan)
    out["주중_비중_pct"] = (out["주중_매출_금액"] / total * 100).round(2)
    out["주말_비중_pct"] = (out["주말_매출_금액"] / total * 100).round(2)
    for col in TIME_COLS:
        short = col.replace("시간대_", "시간_").replace("_매출_금액", "_pct")
        out[short] = (out[col] / total * 100).round(2)
    for col in AGE_COLS:
        short = col.replace("_매출_금액", "_pct")
        out[short] = (out[col] / total * 100).round(2)
    out["남성_비중_pct"] = (out["남성_매출_금액"] / total * 100).round(2)
    out["여성_비중_pct"] = (out["여성_매출_금액"] / total * 100).round(2)
    return out


def analyze_consumer_context(base_quarter: str = "20261", n_clusters: int = 4) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. District-level consumer context (20261)
    sa_dist = pd.read_csv(SALES_DIST_PATH, dtype={"기준_년분기_코드": str, "자치구_코드": str})
    dist_261 = sa_dist[sa_dist["기준_년분기_코드"] == base_quarter].copy()
    dist_ctx = add_context_shares(dist_261)
    keep_cols = [
        "기준_년분기_코드",
        "자치구_코드",
        "자치구_코드_명",
        "당월_매출_금액",
        "당월_매출_건수",
        "주중_비중_pct",
        "주말_비중_pct",
        "시간_00~06_pct",
        "시간_06~11_pct",
        "시간_11~14_pct",
        "시간_14~17_pct",
        "시간_17~21_pct",
        "시간_21~24_pct",
        "연령대_10_pct",
        "연령대_20_pct",
        "연령대_30_pct",
        "연령대_40_pct",
        "연령대_50_pct",
        "연령대_60_이상_pct",
        "남성_비중_pct",
        "여성_비중_pct",
    ]
    dist_ctx[keep_cols].to_csv(
        OUT_DIR / f"seoul_district_consumer_context_{base_quarter}.csv", index=False, encoding="utf-8-sig"
    )

    # 2. Commercial-area (상권) context + KMeans clustering (20261)
    st_comm = pd.read_csv(STORE_COMM_PATH, dtype={"기준_년분기_코드": str, "상권_코드": str})
    sa_comm = pd.read_csv(SALES_COMM_PATH, dtype={"기준_년분기_코드": str, "상권_코드": str})

    st_c = st_comm[st_comm["기준_년분기_코드"] == base_quarter].copy()
    sa_c = sa_comm[sa_comm["기준_년분기_코드"] == base_quarter].copy()
    comm = sa_c.merge(
        st_c[["상권_코드", "전체_점포_수", "일반_점포_수", "프랜차이즈_점포_수"]],
        on="상권_코드",
        how="inner",
    )
    comm = add_context_shares(comm)
    comm["프랜차이즈_비중_pct"] = (comm["프랜차이즈_점포_수"] / comm["전체_점포_수"].replace(0, np.nan) * 100).round(2)
    comm["점포당_매출_원"] = (comm["당월_매출_금액"] / comm["전체_점포_수"].replace(0, np.nan)).round(0)

    feature_cols = [
        "주말_비중_pct",
        "시간_06~11_pct",
        "시간_11~14_pct",
        "시간_14~17_pct",
        "시간_17~21_pct",
        "시간_21~24_pct",
        "연령대_20_pct",
        "연령대_30_pct",
        "연령대_40_pct",
        "연령대_50_pct",
    ]
    valid = comm.dropna(subset=feature_cols).copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(valid[feature_cols])
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    valid["cluster_id"] = km.fit_predict(X_scaled)
    sil = float(silhouette_score(X_scaled, valid["cluster_id"]))

    profile_cols = ["전체_점포_수", "프랜차이즈_비중_pct", "점포당_매출_원"] + feature_cols
    profiles = (
        valid.groupby("cluster_id")[profile_cols]
        .agg(["count", "mean", "median"])
    )
    # Flatten profile table cleanly
    mean_prof = valid.groupby("cluster_id")[profile_cols].mean().round(2)
    mean_prof["commercial_area_count"] = valid.groupby("cluster_id").size()
    mean_prof = mean_prof.reset_index()

    # Assign descriptive empirical labels based on dominant temporal/weekday features
    labels = {}
    for _, r in mean_prof.iterrows():
        cid = int(r["cluster_id"])
        if r["시간_11~14_pct"] == mean_prof["시간_11~14_pct"].max():
            labels[cid] = "오피스·점심 집중형"
        elif r["주말_비중_pct"] == mean_prof["주말_비중_pct"].max():
            labels[cid] = "주말·방문형"
        elif r["시간_17~21_pct"] + r["시간_21~24_pct"] == (mean_prof["시간_17~21_pct"] + mean_prof["시간_21~24_pct"]).max():
            labels[cid] = "저녁·생활형"
        else:
            labels[cid] = "모닝·복합형"

    mean_prof["cluster_label"] = mean_prof["cluster_id"].map(labels)
    valid["cluster_label"] = valid["cluster_id"].map(labels)

    valid[
        [
            "기준_년분기_코드",
            "상권_구분_코드_명",
            "상권_코드",
            "상권_코드_명",
            "전체_점포_수",
            "프랜차이즈_비중_pct",
            "점포당_매출_원",
            "cluster_id",
            "cluster_label",
        ]
        + feature_cols
    ].to_csv(OUT_DIR / f"seoul_commercial_clusters_{base_quarter}.csv", index=False, encoding="utf-8-sig")

    mean_prof.to_csv(OUT_DIR / "seoul_commercial_cluster_profiles.csv", index=False, encoding="utf-8-sig")

    return {
        "base_quarter": base_quarter,
        "district_count": int(len(dist_ctx)),
        "commercial_area_count": int(len(valid)),
        "n_clusters": n_clusters,
        "silhouette_score": round(sil, 4),
        "cluster_summary": mean_prof[
            ["cluster_id", "cluster_label", "commercial_area_count", "주말_비중_pct", "시간_06~11_pct", "시간_11~14_pct", "시간_17~21_pct", "점포당_매출_원"]
        ].to_dict(orient="records"),
    }


def main() -> int:
    import json

    res = analyze_consumer_context()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
