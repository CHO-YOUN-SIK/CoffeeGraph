"""Official Seoul Open Data (서울 열린데이터광장) collector.

Downloads full official CSV datasets via data.seoul.go.kr's HTTPS sheet download
endpoint (datafile.seoul.go.kr), computes SHA-256 checksums, verifies CSV
structure, and records provenance in data/metadata/collection_log.csv and
data/metadata/source_registry.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "datasets.yaml"
COLLECTION_LOG_PATH = ROOT / "data" / "metadata" / "collection_log.csv"
SOURCE_REGISTRY_PATH = ROOT / "data" / "metadata" / "source_registry.csv"

SEOUL_DATASET_KEYS = [
    "seoul_store_district",
    "seoul_sales_district",
    "seoul_store_commercial",
    "seoul_sales_commercial",
]


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["datasets"]


def count_csv_rows_and_cols(path: Path, encoding: str = "cp949") -> tuple[int, int, list[str]]:
    with path.open("r", encoding=encoding, errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        row_count = sum(1 for _ in reader)
    return row_count, len(header), header


def append_collection_log(row: dict[str, Any]) -> None:
    COLLECTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp_utc",
        "dataset_key",
        "dataset_id",
        "dataset_name",
        "status",
        "http_status",
        "row_count",
        "col_count",
        "file_size_bytes",
        "sha256",
        "raw_path",
        "source_url",
        "note",
    ]
    file_exists = COLLECTION_LOG_PATH.exists() and COLLECTION_LOG_PATH.stat().st_size > 0
    with COLLECTION_LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def upsert_source_registry(entries: list[dict[str, Any]]) -> None:
    SOURCE_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "dataset_key",
        "dataset_id",
        "dataset_name",
        "api_service",
        "source_url",
        "download_url",
        "encoding",
        "license",
        "raw_path",
        "last_collected_utc",
        "row_count",
        "col_count",
        "file_size_bytes",
        "sha256",
        "status",
    ]
    existing: dict[str, dict[str, Any]] = {}
    if SOURCE_REGISTRY_PATH.exists() and SOURCE_REGISTRY_PATH.stat().st_size > 0:
        with SOURCE_REGISTRY_PATH.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                existing[r["dataset_key"]] = r
    for entry in entries:
        existing[entry["dataset_key"]] = entry
    with SOURCE_REGISTRY_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(existing.keys()):
            writer.writerow(existing[key])


def download_seoul_dataset(key: str, cfg: dict[str, Any], timeout: int = 300) -> dict[str, Any]:
    raw_path = ROOT / cfg["raw_path"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = raw_path.with_suffix(".csv.tmp")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; CoffeeOpportunityResearch/0.1)",
            "Referer": cfg["source_url"],
        }
    )

    payload = {
        "srvType": cfg.get("srv_type", "S"),
        "infId": cfg["id"],
        "serviceKind": cfg.get("service_kind", "1"),
        "pageNo": "1",
        "ssUserId": "SAMPLE_VIEW",
        "strWhere": "",
        "strOrderby": "STDR_YYQU_CD DESC",
    }

    ts = datetime.now(timezone.utc).isoformat()
    resp = session.post(cfg["download_url"], data=payload, stream=True, timeout=timeout)
    if resp.status_code != 200:
        err_msg = f"HTTP {resp.status_code}: {resp.text[:300]}"
        append_collection_log(
            {
                "timestamp_utc": ts,
                "dataset_key": key,
                "dataset_id": cfg["id"],
                "dataset_name": cfg["name"],
                "status": "FAILED",
                "http_status": resp.status_code,
                "row_count": 0,
                "col_count": 0,
                "file_size_bytes": 0,
                "sha256": "",
                "raw_path": cfg["raw_path"],
                "source_url": cfg["source_url"],
                "note": err_msg,
            }
        )
        raise RuntimeError(f"Failed to download {key} ({cfg['id']}): {err_msg}")

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        body_preview = resp.text[:300]
        raise RuntimeError(f"Unexpected HTML response for {key} ({cfg['id']}): {body_preview}")

    hasher = hashlib.sha256()
    total_bytes = 0
    with tmp_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)
                hasher.update(chunk)
                total_bytes += len(chunk)

    if total_bytes == 0:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded 0 bytes for {key} ({cfg['id']})")

    os.replace(tmp_path, raw_path)
    sha256 = hasher.hexdigest()
    encoding = cfg.get("encoding", "cp949")
    row_count, col_count, header = count_csv_rows_and_cols(raw_path, encoding=encoding)

    if row_count == 0 or col_count == 0:
        raise RuntimeError(f"Empty CSV parsed for {key} ({cfg['id']}): rows={row_count}, cols={col_count}")

    note = f"Downloaded full official CSV; first_col={header[0] if header else ''}"
    append_collection_log(
        {
            "timestamp_utc": ts,
            "dataset_key": key,
            "dataset_id": cfg["id"],
            "dataset_name": cfg["name"],
            "status": "SUCCESS",
            "http_status": resp.status_code,
            "row_count": row_count,
            "col_count": col_count,
            "file_size_bytes": total_bytes,
            "sha256": sha256,
            "raw_path": cfg["raw_path"],
            "source_url": cfg["source_url"],
            "note": note,
        }
    )

    return {
        "dataset_key": key,
        "dataset_id": cfg["id"],
        "dataset_name": cfg["name"],
        "api_service": cfg.get("api_service", ""),
        "source_url": cfg["source_url"],
        "download_url": cfg["download_url"],
        "encoding": encoding,
        "license": cfg.get("license", ""),
        "raw_path": cfg["raw_path"],
        "last_collected_utc": ts,
        "row_count": row_count,
        "col_count": col_count,
        "file_size_bytes": total_bytes,
        "sha256": sha256,
        "status": "COLLECTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect official Seoul Open Data datasets.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=SEOUL_DATASET_KEYS,
        choices=SEOUL_DATASET_KEYS,
        help="Dataset keys to collect.",
    )
    args = parser.parse_args()

    all_cfg = load_config()
    registry_updates: list[dict[str, Any]] = []
    for key in args.datasets:
        print(f"[seoul_open_data] Downloading {key} ({all_cfg[key]['id']})...")
        entry = download_seoul_dataset(key, all_cfg[key])
        registry_updates.append(entry)
        print(
            f"[seoul_open_data] OK {key}: rows={entry['row_count']:,}, "
            f"cols={entry['col_count']}, size={entry['file_size_bytes']:,} bytes, "
            f"sha256={entry['sha256'][:12]}..."
        )

    upsert_source_registry(registry_updates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
