"""Phase 2: Official Data Validation for Seoul Open Data & CQI datasets.

Validates full raw files (never samples), checks schema, row counts, missingness,
duplicates, quarter coverage, district/industry codes, store-count arithmetic,
sales-sum consistency, and spatial boundary stability. Writes results to
data/metadata/validation_results.json and exits non-zero on failure.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATASETS_CFG_PATH = ROOT / "config" / "datasets.yaml"
SCOPE_CFG_PATH = ROOT / "config" / "research_scope.yaml"
VALIDATION_OUT_PATH = ROOT / "data" / "metadata" / "validation_results.json"

STORE_COMMON_COLS = [
    "기준_년분기_코드",
    "서비스_업종_코드",
    "서비스_업종_코드_명",
    "전체_점포_수",
    "일반_점포_수",
    "프랜차이즈_점포_수",
    "개업_율",
    "개업_점포_수",
    "폐업_률",
    "폐업_점포_수",
]

SPATIAL_COLS = {
    "자치구_코드": ["자치구_코드", "자치구_코드_명"],
    "상권_코드": ["상권_구분_코드", "상권_구분_코드_명", "상권_코드", "상권_코드_명"],
}

SALES_DISTRICT_REQUIRED_COLS = [
    "기준_년분기_코드",
    "자치구_코드",
    "자치구_코드_명",
    "서비스_업종_코드",
    "서비스_업종_코드_명",
    "당월_매출_금액",
    "당월_매출_건수",
    "주중_매출_금액",
    "주말_매출_금액",
    "월요일_매출_금액",
    "화요일_매출_금액",
    "수요일_매출_금액",
    "목요일_매출_금액",
    "금요일_매출_금액",
    "토요일_매출_금액",
    "일요일_매출_금액",
    "시간대_00~06_매출_금액",
    "시간대_06~11_매출_금액",
    "시간대_11~14_매출_금액",
    "시간대_14~17_매출_금액",
    "시간대_17~21_매출_금액",
    "시간대_21~24_매출_금액",
]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_store_df(
    df: pd.DataFrame,
    key_col: str,
    expected_quarters: list[str],
    industry_code: str,
    expected_districts: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    expected_cols = STORE_COMMON_COLS + SPATIAL_COLS.get(key_col, [key_col])
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")

    quarters = sorted(df["기준_년분기_코드"].dropna().astype(str).unique().tolist())
    missing_quarters = [q for q in expected_quarters if q not in quarters]
    if missing_quarters:
        errors.append(f"Missing target quarters: {missing_quarters}")

    cs_df = df[df["서비스_업종_코드"].astype(str) == industry_code].copy()
    if cs_df.empty:
        errors.append(f"No rows found for industry_code={industry_code}")

    dup_count = int(df.duplicated(subset=["기준_년분기_코드", key_col, "서비스_업종_코드"]).sum())
    if dup_count > 0:
        errors.append(f"Duplicate key rows: {dup_count}")

    cs_units = int(cs_df[key_col].nunique())
    if expected_districts is not None and cs_units != expected_districts:
        errors.append(f"Expected {expected_districts} districts for {industry_code}, got {cs_units}")

    # Store count consistency: 전체_점포_수 == 일반_점포_수 + 프랜차이즈_점포_수
    diff = (
        pd.to_numeric(cs_df["전체_점포_수"], errors="coerce")
        - (
            pd.to_numeric(cs_df["일반_점포_수"], errors="coerce")
            + pd.to_numeric(cs_df["프랜차이즈_점포_수"], errors="coerce")
        )
    ).abs()
    max_store_diff = float(diff.max()) if not diff.empty else 0.0
    if max_store_diff > 1e-6:
        errors.append(f"Store count mismatch (전체 != 일반 + 프랜차이즈), max_diff={max_store_diff}")

    # Spatial boundary stability across comparison quarters
    q_units: dict[str, set[str]] = {}
    for q in expected_quarters:
        sub = cs_df[cs_df["기준_년분기_코드"].astype(str) == q]
        q_units[q] = set(sub[key_col].astype(str).unique())
    unit_counts = {q: len(s) for q, s in q_units.items()}
    base_set = q_units.get(expected_quarters[0], set())
    boundary_changed = any(s != base_set for s in q_units.values())
    if boundary_changed:
        warnings.append(f"Spatial unit set varies across quarters: {unit_counts}")

    missing_rates = {col: round(float(df[col].isna().mean()), 6) for col in df.columns}

    return {
        "status": "VALIDATED" if not errors else "FAILED",
        "total_rows": int(len(df)),
        "total_cols": int(df.shape[1]),
        "cs100010_rows": int(len(cs_df)),
        "cs100010_spatial_units": cs_units,
        "quarters_available": quarters,
        "duplicate_key_rows": dup_count,
        "max_store_sum_diff": max_store_diff,
        "boundary_changed_across_target_quarters": boundary_changed,
        "target_quarter_unit_counts": unit_counts,
        "max_missing_rate": max(missing_rates.values()) if missing_rates else 0.0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_sales_df(
    df: pd.DataFrame,
    key_col: str,
    expected_quarters: list[str],
    industry_code: str,
    expected_districts: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    req = [c for c in SALES_DISTRICT_REQUIRED_COLS if c != "자치구_코드" and c != "자치구_코드_명"] + [key_col]
    missing_cols = [c for c in req if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required sales columns: {missing_cols}")

    quarters = sorted(df["기준_년분기_코드"].dropna().astype(str).unique().tolist())
    missing_quarters = [q for q in expected_quarters if q not in quarters]
    if missing_quarters:
        errors.append(f"Missing target quarters: {missing_quarters}")

    cs_df = df[df["서비스_업종_코드"].astype(str) == industry_code].copy()
    if cs_df.empty:
        errors.append(f"No rows found for industry_code={industry_code}")

    dup_count = int(df.duplicated(subset=["기준_년분기_코드", key_col, "서비스_업종_코드"]).sum())
    if dup_count > 0:
        errors.append(f"Duplicate key rows: {dup_count}")

    cs_units = int(cs_df[key_col].nunique())
    if expected_districts is not None and cs_units != expected_districts:
        errors.append(f"Expected {expected_districts} districts for {industry_code}, got {cs_units}")

    # Sales sum consistency checks on CS100010
    total_amt = pd.to_numeric(cs_df["당월_매출_금액"], errors="coerce")
    wk_sum = pd.to_numeric(cs_df["주중_매출_금액"], errors="coerce") + pd.to_numeric(
        cs_df["주말_매출_금액"], errors="coerce"
    )
    day_cols = [
        "월요일_매출_금액",
        "화요일_매출_금액",
        "수요일_매출_금액",
        "목요일_매출_금액",
        "금요일_매출_금액",
        "토요일_매출_금액",
        "일요일_매출_금액",
    ]
    day_sum = cs_df[day_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    time_cols = [
        "시간대_00~06_매출_금액",
        "시간대_06~11_매출_금액",
        "시간대_11~14_매출_금액",
        "시간대_14~17_매출_금액",
        "시간대_17~21_매출_금액",
        "시간대_21~24_매출_금액",
    ]
    time_sum = cs_df[time_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

    max_wk_rel_diff = float(((total_amt - wk_sum).abs() / total_amt.replace(0, np.nan)).max())
    max_day_rel_diff = float(((total_amt - day_sum).abs() / total_amt.replace(0, np.nan)).max())
    max_time_rel_diff = float(((total_amt - time_sum).abs() / total_amt.replace(0, np.nan)).max())

    if max_wk_rel_diff > 1e-4:
        warnings.append(f"Weekday+Weekend sales rel diff={max_wk_rel_diff:.6f}")
    if max_day_rel_diff > 1e-4:
        warnings.append(f"7-day sales sum rel diff={max_day_rel_diff:.6f}")
    if max_time_rel_diff > 1e-4:
        warnings.append(f"6-timeslot sales sum rel diff={max_time_rel_diff:.6f}")

    missing_rates = {col: round(float(df[col].isna().mean()), 6) for col in df.columns}

    return {
        "status": "VALIDATED" if not errors else "FAILED",
        "total_rows": int(len(df)),
        "total_cols": int(df.shape[1]),
        "cs100010_rows": int(len(cs_df)),
        "cs100010_spatial_units": cs_units,
        "quarters_available": quarters,
        "duplicate_key_rows": dup_count,
        "max_weekday_weekend_rel_diff": round(max_wk_rel_diff, 8) if not np.isnan(max_wk_rel_diff) else 0.0,
        "max_7day_rel_diff": round(max_day_rel_diff, 8) if not np.isnan(max_day_rel_diff) else 0.0,
        "max_6timeslot_rel_diff": round(max_time_rel_diff, 8) if not np.isnan(max_time_rel_diff) else 0.0,
        "max_missing_rate": max(missing_rates.values()) if missing_rates else 0.0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_cqi_df(df: pd.DataFrame, expected_species: str) -> dict[str, Any]:
    errors: list[str] = []
    if "Total.Cup.Points" not in df.columns:
        errors.append("Missing Total.Cup.Points column")
    if "Country.of.Origin" not in df.columns:
        errors.append("Missing Country.of.Origin column")
    if "Processing.Method" not in df.columns:
        errors.append("Missing Processing.Method column")
    return {
        "status": "VALIDATED" if not errors else "FAILED",
        "expected_species": expected_species,
        "total_rows": int(len(df)),
        "total_cols": int(df.shape[1]),
        "zero_cup_points_rows": int((pd.to_numeric(df["Total.Cup.Points"], errors="coerce") <= 0).sum())
        if "Total.Cup.Points" in df.columns
        else None,
        "errors": errors,
        "warnings": [],
    }


def run_validation(require_commercial: bool = False) -> dict[str, Any]:
    datasets_cfg = load_yaml(DATASETS_CFG_PATH)["datasets"]
    scope_cfg = load_yaml(SCOPE_CFG_PATH)
    expected_quarters: list[str] = scope_cfg["seoul_market"]["comparison_quarters"]
    industry_code: str = scope_cfg["seoul_market"]["industry_code"]
    expected_districts: int = scope_cfg["seoul_market"]["expected_district_count"]

    results: dict[str, Any] = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": "VALIDATED",
        "datasets": {},
    }

    commercial_quarters = [q for q in expected_quarters if q >= "20251"]
    checks = [
        ("seoul_store_district", "store", "자치구_코드", expected_districts, expected_quarters, True),
        ("seoul_sales_district", "sales", "자치구_코드", expected_districts, expected_quarters, True),
        ("seoul_store_commercial", "store", "상권_코드", None, commercial_quarters, require_commercial),
        ("seoul_sales_commercial", "sales", "상권_코드", None, commercial_quarters, require_commercial),
    ]

    any_failed = False
    for key, kind, spatial_col, exp_dist, q_list, required in checks:
        cfg = datasets_cfg[key]
        raw_path = ROOT / cfg["raw_path"]
        if not raw_path.exists():
            status = "BLOCKED_SOURCE_NOT_AVAILABLE" if required else "SKIPPED_NOT_DOWNLOADED"
            results["datasets"][key] = {"status": status, "raw_path": cfg["raw_path"]}
            if required:
                any_failed = True
            continue

        df = pd.read_csv(
            raw_path,
            encoding=cfg.get("encoding", "cp949"),
            dtype={"기준_년분기_코드": str, spatial_col: str, "서비스_업종_코드": str},
            low_memory=False,
        )
        if kind == "store":
            res = validate_store_df(df, spatial_col, q_list, industry_code, exp_dist)
        else:
            res = validate_sales_df(df, spatial_col, q_list, industry_code, exp_dist)
        results["datasets"][key] = res
        if res["status"] != "VALIDATED":
            any_failed = True

    for cqi_key, sp in [("cqi_arabica", "Arabica"), ("cqi_robusta", "Robusta")]:
        cfg = datasets_cfg[cqi_key]
        raw_path = ROOT / cfg["raw_path"]
        if not raw_path.exists():
            results["datasets"][cqi_key] = {"status": "BLOCKED_SOURCE_NOT_AVAILABLE", "raw_path": cfg["raw_path"]}
            any_failed = True
            continue
        df = pd.read_csv(raw_path, encoding=cfg.get("encoding", "utf-8"))
        res = validate_cqi_df(df, sp)
        results["datasets"][cqi_key] = res
        if res["status"] != "VALIDATED":
            any_failed = True

    results["overall_status"] = "FAILED" if any_failed else "VALIDATED"
    VALIDATION_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def main() -> int:
    res = run_validation(require_commercial=False)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["overall_status"] == "VALIDATED" else 1


if __name__ == "__main__":
    sys.exit(main())
