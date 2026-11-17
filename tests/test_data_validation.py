"""Tests for Phase 2 official data validation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.cleaning.validate_seoul import (
    ROOT,
    VALIDATION_OUT_PATH,
    run_validation,
    validate_cqi_df,
    validate_store_df,
)


def test_validation_passes_on_committed_datasets() -> None:
    res = run_validation(require_commercial=False)
    assert res["overall_status"] == "VALIDATED"
    assert res["datasets"]["seoul_store_district"]["status"] == "VALIDATED"
    assert res["datasets"]["seoul_sales_district"]["status"] == "VALIDATED"
    assert res["datasets"]["cqi_arabica"]["status"] == "VALIDATED"
    assert res["datasets"]["cqi_robusta"]["status"] == "VALIDATED"
    assert VALIDATION_OUT_PATH.exists()
    saved = json.loads(VALIDATION_OUT_PATH.read_text(encoding="utf-8"))
    assert saved["overall_status"] == "VALIDATED"


def test_validate_store_df_detects_store_sum_mismatch() -> None:
    df = pd.DataFrame(
        {
            "기준_년분기_코드": ["20261"],
            "자치구_코드": ["11110"],
            "자치구_코드_명": ["종로구"],
            "서비스_업종_코드": ["CS100010"],
            "서비스_업종_코드_명": ["커피-음료"],
            "전체_점포_수": [100.0],
            "일반_점포_수": [70.0],
            "프랜차이즈_점포_수": [20.0],  # 70 + 20 != 100
            "개업_율": [1.0],
            "개업_점포_수": [1.0],
            "폐업_률": [1.0],
            "폐업_점포_수": [1.0],
        }
    )
    res = validate_store_df(df, "자치구_코드", ["20261"], "CS100010", expected_districts=1)
    assert res["status"] == "FAILED"
    assert any("Store count mismatch" in e for e in res["errors"])


def test_validate_cqi_df_requires_core_columns() -> None:
    df = pd.DataFrame({"Total.Cup.Points": [84.5]})
    res = validate_cqi_df(df, "Arabica")
    assert res["status"] == "FAILED"
    assert len(res["errors"]) == 2
