"""Commercial-Area External Context Collector (Seoul Open Data).

Collects official commercial-area population datasets:
- OA-15569: 직장인구-상권 (Work Population)
- OA-15568: 길단위인구-상권 (Foot Traffic / Living Population)
- OA-15584: 상주인구-상권 (Resident Population)

Validates uniqueness on (기준_년분기_코드, 상권_코드), audits annual-update
cadence (comparing 20261 vs 20251 identical-value rate), and writes the
clean 20261 commercial-area context table to data/processed/seoul/commercial_context_20261.csv.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.collectors.seoul_open_data import (
    download_seoul_dataset,
    load_config,
    upsert_source_registry,
)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_SEOUL_DIR = ROOT / "data" / "processed" / "seoul"
METADATA_DIR = ROOT / "data" / "metadata"

CONTEXT_KEYS = [
    "seoul_work_pop_commercial",
    "seoul_foot_pop_commercial",
    "seoul_res_pop_commercial",
]


def _check_annual_cadence(df: pd.DataFrame, val_col: str) -> dict[str, Any]:
    """Check whether 20261 and 20251 values are identical (annual-update indicator)."""
    q26 = df[df["기준_년분기_코드"].astype(str) == "20261"][["상권_코드", val_col]].drop_duplicates("상권_코드")
    q25 = df[df["기준_년분기_코드"].astype(str) == "20251"][["상권_코드", val_col]].drop_duplicates("상권_코드")
    if q26.empty or q25.empty:
        return {"compared": 0, "identical_pct": None}
    m = q26.merge(q25, on="상권_코드", suffixes=("_26", "_25"))
    same = int((m[f"{val_col}_26"] == m[f"{val_col}_25"]).sum())
    return {
        "compared": int(len(m)),
        "identical_count": same,
        "identical_pct": round(same / len(m) * 100, 1) if len(m) else 0.0,
    }


def collect_and_process_seoul_context(quarter: str = "20261") -> dict[str, Any]:
    PROCESSED_SEOUL_DIR.mkdir(parents=True, exist_ok=True)
    cfg_all = load_config()

    registry_entries = []
    for k in CONTEXT_KEYS:
        entry = download_seoul_dataset(k, cfg_all[k])
        registry_entries.append(entry)
    upsert_source_registry(registry_entries)

    work_df = pd.read_csv(ROOT / cfg_all["seoul_work_pop_commercial"]["raw_path"], encoding="cp949")
    foot_df = pd.read_csv(ROOT / cfg_all["seoul_foot_pop_commercial"]["raw_path"], encoding="cp949")
    res_df = pd.read_csv(ROOT / cfg_all["seoul_res_pop_commercial"]["raw_path"], encoding="cp949")

    cadence_audit = {
        "work_pop_20261_vs_20251": _check_annual_cadence(work_df, "총_직장_인구_수"),
        "foot_pop_20261_vs_20251": _check_annual_cadence(foot_df, "총_유동인구_수"),
        "res_pop_20261_vs_20251": _check_annual_cadence(res_df, "총_상주인구_수"),
    }

    w26 = work_df[work_df["기준_년분기_코드"].astype(str) == quarter].copy()
    f26 = foot_df[foot_df["기준_년분기_코드"].astype(str) == quarter].copy()
    r26 = res_df[res_df["기준_년분기_코드"].astype(str) == quarter].copy()

    # Enforce join key uniqueness on 상권_코드
    assert w26["상권_코드"].is_unique, "Duplicate 상권_코드 in work_pop 20261"
    assert f26["상권_코드"].is_unique, "Duplicate 상권_코드 in foot_pop 20261"
    assert r26["상권_코드"].is_unique, "Duplicate 상권_코드 in res_pop 20261"

    w_keep = w26[["상권_코드", "총_직장_인구_수", "연령대_20_직장_인구_수", "연령대_30_직장_인구_수"]].copy()
    f_keep = f26[
        [
            "상권_코드",
            "총_유동인구_수",
            "시간대_11_14_유동인구_수",
            "시간대_17_21_유동인구_수",
            "토요일_유동인구_수",
            "일요일_유동인구_수",
        ]
    ].copy()
    f_keep["주말_유동인구_비중"] = (
        (f_keep["토요일_유동인구_수"] + f_keep["일요일_유동인구_수"])
        / f_keep["총_유동인구_수"].replace(0, pd.NA)
        * 100
    ).round(2)
    f_keep["점심_유동인구_비중"] = (
        f_keep["시간대_11_14_유동인구_수"] / f_keep["총_유동인구_수"].replace(0, pd.NA) * 100
    ).round(2)

    r_keep = r26[["상권_코드", "총_상주인구_수", "총_가구_수", "아파트_가구_수"]].copy()

    merged = (
        f_keep.merge(w_keep, on="상권_코드", how="outer")
        .merge(r_keep, on="상권_코드", how="outer")
        .sort_values("상권_코드")
        .reset_index(drop=True)
    )
    out_csv = PROCESSED_SEOUL_DIR / f"commercial_context_{quarter}.csv"
    merged.to_csv(out_csv, index=False, encoding="utf-8-sig")

    summary = {
        "quarter": quarter,
        "output_csv": str(out_csv.relative_to(ROOT)),
        "commercial_areas_total": int(len(merged)),
        "work_pop_areas": int(len(w_keep)),
        "foot_pop_areas": int(len(f_keep)),
        "res_pop_areas": int(len(r_keep)),
        "cadence_audit": cadence_audit,
    }
    (METADATA_DIR / "seoul_context_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    res = collect_and_process_seoul_context("20261")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
