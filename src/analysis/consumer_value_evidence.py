"""Track D: auditable public consumer survey signals, not invented X/Y/Z coordinates.

Public aggregate indicators come from a survey publisher's article and remain
separated by question_construct and denominator notes. Never average these
percentages across questions or compare directly to brand-text coordinates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IN_PATH = ROOT / "data" / "curated" / "consumer" / "opensurvey_cafe_2025_public_metrics.csv"
OUT_PATH = ROOT / "outputs" / "tables" / "consumer_value_evidence.json"

REQUIRED = {
    "metric_id", "source_id", "year", "publication_date", "population",
    "question_construct", "dimension_hint", "metric_label", "percent",
    "denominator_note", "source_url", "interpretation_guard",
}


def build_consumer_value_evidence() -> dict:
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig")
    missing_cols = REQUIRED.difference(df.columns)
    if missing_cols:
        raise ValueError(f"Missing consumer evidence fields: {sorted(missing_cols)}")
    if df["metric_id"].isna().any() or df["metric_id"].duplicated().any():
        raise ValueError("Survey metric IDs must be present and unique")
    if not pd.to_numeric(df["percent"], errors="coerce").between(0, 100).all():
        raise ValueError("Survey percentages must be valid [0, 100] values")
    if not df["source_url"].astype(str).str.startswith("https://").all():
        raise ValueError("Every indicator requires a direct official source URL")
    if df["question_construct"].isna().any() or df["denominator_note"].isna().any():
        raise ValueError("Question construct and denominator caveats are mandatory")
    # An item's interpretive bucket is metadata, not a coordinate or comparable scale.
    allowed_hints = {"practical", "sensory", "experience", "philosophical"}
    if not set(df["dimension_hint"].astype(str)).issubset(allowed_hints):
        raise ValueError("Unknown survey construct hint")
    if df["question_construct"].astype(str).str.strip().eq("").any():
        raise ValueError("The survey question/construct may not be empty")

    items = []
    for record in df.to_dict(orient="records"):
        record["percent"] = round(float(record["percent"]), 2)
        record["year"] = int(record["year"])
        items.append(record)

    out = {
        "status": "PUBLIC_AGGREGATES_ONLY",
        "study": "Opensurvey Cafe Trend Report 2025",
        "metric_count": len(items),
        "source": "https://blog.opensurvey.co.kr/article/cafe-2025-2/",
        "sample_context": "National adults aged 20–59; reported two-phase survey; verify each item's base in full report.",
        "epistemological_rule": (
            "Separate question constructs. No synthetic respondent-level observations; "
            "no consumer X/Y/Z coordinates; no numeric consumer-brand fit scores."
        ),
        "unknown_axes": ["consumer_x_practical_composite", "consumer_y_sensory_composite", "consumer_z_philosophical_composite"],
        "metrics": items,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> None:
    result = build_consumer_value_evidence()
    print(f"Public consumer signals validated: {result['metric_count']} metrics -> {OUT_PATH}")
    print("Consumer X/Y/Z withheld: incompatible question bases and missing values.")


if __name__ == "__main__":
    main()
