"""Tests for Track C: 3D Brand Value Space (Practical x Sensory x Philosophical)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_official_brand_philosophy_raw_has_all_brands() -> None:
    path = ROOT / "data" / "raw" / "brands" / "official_brand_philosophy_raw.csv"
    assert path.exists()
    from src.analysis.value_space import compute_brand_value_space

    df, _ = compute_brand_value_space()
    assert len(df) == 8
    assert df["brand_id"].nunique() == 8
    assert (df["text_length"] > 0).all()


def test_value_space_brands_table_valid() -> None:
    path = ROOT / "outputs" / "tables" / "value_space_brands.csv"
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 8
    for col in ("x_practical", "y_sensory"):
        assert df[col].notna().all()
        assert df[col].between(0, 100).all()
    assert df["z_philosophical"].dropna().between(0, 100).all()
    assert set(df["z_disclosure_tier"]).issubset(
        {"Rich Disclosure", "Moderate Disclosure", "Minimal / Unstated", "Insufficient Source Text"}
    )
    # Coffee Libre should rank top on Z due to B Corp + Direct Trade + Finca Libre disclosure
    top_z = df.sort_values("z_philosophical", ascending=False).iloc[0]["brand_id"]
    assert top_z == "coffee_libre"
    for bid in ("terarosa", "center_coffee"):
        row = df[df["brand_id"] == bid].iloc[0]
        assert pd.isna(row["z_philosophical"])
        assert row["z_disclosure_tier"] == "Insufficient Source Text"


def test_consumer_value_schema_and_artifacts_exist() -> None:
    schema_path = ROOT / "data" / "metadata" / "consumer_value_schema.json"
    assert schema_path.exists()
    from src.analysis.value_space import build_consumer_value_schema

    # Validate the current schema source, not a previously committed generated artifact.
    schema = build_consumer_value_schema()
    assert schema["epistemological_rule"] == "Visual Juxtaposition Only — Not Consumer-Brand Fit"
    assert set(schema["dimensions"].keys()) == {"x_practical", "y_sensory", "z_philosophical"}
    assert schema["consumer_observed_evidence"]["consumer_xyz_status"] == "NOT_ESTIMABLE_FROM_CURRENT_AGGREGATES"

    html_path = ROOT / "outputs" / "figures" / "coffee_value_space_3d.html"
    png_path = ROOT / "outputs" / "figures" / "fig07_brand_value_space_3d.png"
    assert html_path.exists() and html_path.stat().st_size > 5000
    assert png_path.exists() and png_path.stat().st_size > 10000


def test_public_consumer_evidence_is_real_not_synthetic_xyz() -> None:
    from src.analysis.consumer_value_evidence import build_consumer_value_evidence

    evidence = build_consumer_value_evidence()
    assert evidence["status"] == "PUBLIC_AGGREGATES_ONLY"
    assert evidence["metric_count"] == 5
    assert len(evidence["unknown_axes"]) == 3
    d = {i["metric_id"]: i["percent"] for i in evidence["metrics"]}
    assert d["customization_ever"] == 82.4
    assert d["premium_coffee_quality"] == 58.4
    assert "consumer_xyz" not in evidence
    assert not any("brand_id" in i for i in evidence["metrics"])


def test_brand_3d_excludes_made_up_consumer_positions() -> None:
    from src.visualization.value_space_3d import build_plotly_3d

    from src.analysis.value_space import compute_brand_value_space

    df, _ = compute_brand_value_space()
    fig = build_plotly_3d(df)
    assert not any("Consumer Field" in str(getattr(trace, "name", "")) for trace in fig.data)
    assert all(pd.notna(z) for trace in fig.data
               for z in list(getattr(trace, "z", []) if getattr(trace, "z", None) is not None else []))
