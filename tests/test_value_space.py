"""Tests for Track C: 3D Brand Value Space (Practical x Sensory x Philosophical)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_official_brand_philosophy_raw_has_all_brands() -> None:
    path = ROOT / "data" / "raw" / "brands" / "official_brand_philosophy_raw.csv"
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 8
    assert df["brand_id"].nunique() == 8
    assert (df["text_length"] > 0).all()


def test_value_space_brands_table_valid() -> None:
    path = ROOT / "outputs" / "tables" / "value_space_brands.csv"
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 8
    for col in ("x_practical", "y_sensory", "z_philosophical"):
        assert df[col].notna().all()
        assert (df[col] >= 0.0).all() and (df[col] <= 100.0).all()
    assert set(df["z_disclosure_tier"]).issubset(
        {"Rich Disclosure", "Moderate Disclosure", "Minimal / Unstated"}
    )
    # Coffee Libre should rank top on Z due to B Corp + Direct Trade + Finca Libre disclosure
    top_z = df.sort_values("z_philosophical", ascending=False).iloc[0]["brand_id"]
    assert top_z == "coffee_libre"


def test_consumer_value_schema_and_artifacts_exist() -> None:
    schema_path = ROOT / "data" / "metadata" / "consumer_value_schema.json"
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["epistemological_rule"] == "Visual Juxtaposition Only — Not Consumer-Brand Fit"
    assert set(schema["dimensions"].keys()) == {"x_practical", "y_sensory", "z_philosophical"}

    html_path = ROOT / "outputs" / "figures" / "coffee_value_space_3d.html"
    png_path = ROOT / "outputs" / "figures" / "fig07_brand_value_space_3d.png"
    assert html_path.exists() and html_path.stat().st_size > 5000
    assert png_path.exists() and png_path.stat().st_size > 10000
