"""Build clean processed datasets for CS100010 (커피-음료) and CQI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_seoul_processed() -> dict[str, int]:
    datasets = load_yaml(ROOT / "config" / "datasets.yaml")["datasets"]
    scope = load_yaml(ROOT / "config" / "research_scope.yaml")
    industry_code = scope["seoul_market"]["industry_code"]

    out_dir = ROOT / "data" / "processed" / "seoul"
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    mapping = [
        ("seoul_store_district", "자치구_코드", "cs100010_store_district.csv"),
        ("seoul_sales_district", "자치구_코드", "cs100010_sales_district.csv"),
        ("seoul_store_commercial", "상권_코드", "cs100010_store_commercial.csv"),
        ("seoul_sales_commercial", "상권_코드", "cs100010_sales_commercial.csv"),
    ]

    for key, spatial_col, out_name in mapping:
        cfg = datasets[key]
        raw_path = ROOT / cfg["raw_path"]
        if not raw_path.exists():
            continue
        df = pd.read_csv(
            raw_path,
            encoding=cfg.get("encoding", "cp949"),
            dtype={"기준_년분기_코드": str, spatial_col: str, "서비스_업종_코드": str},
            low_memory=False,
        )
        sub = df[df["서비스_업종_코드"] == industry_code].copy()
        sub = sub.sort_values(["기준_년분기_코드", spatial_col]).reset_index(drop=True)
        sub.to_csv(out_dir / out_name, index=False, encoding="utf-8-sig")
        counts[out_name] = len(sub)
    return counts


def build_cqi_processed() -> int:
    datasets = load_yaml(ROOT / "config" / "datasets.yaml")["datasets"]
    out_dir = ROOT / "data" / "processed" / "cqi"
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for key, sp in [("cqi_arabica", "Arabica"), ("cqi_robusta", "Robusta")]:
        raw_path = ROOT / datasets[key]["raw_path"]
        df = pd.read_csv(raw_path, encoding="utf-8")
        df["Species_Source"] = sp
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(out_dir / "cqi_combined.csv", index=False, encoding="utf-8-sig")
    return len(combined)


def main() -> int:
    seoul_counts = build_seoul_processed()
    cqi_count = build_cqi_processed()
    print("Processed Seoul CS100010:", seoul_counts)
    print("Processed CQI combined:", cqi_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
