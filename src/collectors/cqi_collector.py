"""Official CQI Coffee Quality Database collector.

Downloads arabica_data_cleaned.csv and robusta_data_cleaned.csv from
https://github.com/jldbc/coffee-quality-database and records SHA-256 checksums
and provenance in data/metadata/.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.collectors.seoul_open_data import (
    ROOT,
    append_collection_log,
    count_csv_rows_and_cols,
    load_config,
    upsert_source_registry,
)

CQI_KEYS = ["cqi_arabica", "cqi_robusta"]


def download_cqi_dataset(key: str, cfg: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    raw_path = ROOT / cfg["raw_path"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = raw_path.with_suffix(".csv.tmp")

    ts = datetime.now(timezone.utc).isoformat()
    resp = requests.get(cfg["download_url"], timeout=timeout)
    if resp.status_code != 200:
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
                "note": f"HTTP {resp.status_code}",
            }
        )
        raise RuntimeError(f"Failed to download {key}: HTTP {resp.status_code}")

    content = resp.content
    sha256 = hashlib.sha256(content).hexdigest()
    tmp_path.write_bytes(content)
    os.replace(tmp_path, raw_path)

    row_count, col_count, header = count_csv_rows_and_cols(raw_path, encoding=cfg.get("encoding", "utf-8"))
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
            "file_size_bytes": len(content),
            "sha256": sha256,
            "raw_path": cfg["raw_path"],
            "source_url": cfg["source_url"],
            "note": f"Downloaded CQI CSV; cols={col_count}",
        }
    )

    return {
        "dataset_key": key,
        "dataset_id": cfg["id"],
        "dataset_name": cfg["name"],
        "api_service": "",
        "source_url": cfg["source_url"],
        "download_url": cfg["download_url"],
        "encoding": cfg.get("encoding", "utf-8"),
        "license": cfg.get("license", ""),
        "raw_path": cfg["raw_path"],
        "last_collected_utc": ts,
        "row_count": row_count,
        "col_count": col_count,
        "file_size_bytes": len(content),
        "sha256": sha256,
        "status": "COLLECTED",
    }


def main() -> int:
    all_cfg = load_config()
    updates: list[dict[str, Any]] = []
    for key in CQI_KEYS:
        print(f"[cqi_collector] Downloading {key}...")
        entry = download_cqi_dataset(key, all_cfg[key])
        updates.append(entry)
        print(
            f"[cqi_collector] OK {key}: rows={entry['row_count']:,}, "
            f"cols={entry['col_count']}, sha256={entry['sha256'][:12]}..."
        )
    upsert_source_registry(updates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
