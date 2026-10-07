"""Download and profile the Our World in Data compact COVID-19 CSV.

Phase 2 goal: learn the real file — columns, grain, nulls, duplicates,
aggregates, and limitations — before writing the ingestion pipeline.

This script is intentionally read-only toward PostgreSQL. It does not load
a warehouse. Re-run it whenever the remote file changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.utils.config import (
    OWID_COVID_URL,
    PROCESSED_DATA_DIR,
    RAW_CSV_NAME,
    RAW_DATA_DIR,
)
from src.utils.logger import get_logger

logger = get_logger("exploration.profile_source")

PROFILE_COLUMNS = [
    "country",
    "date",
    "total_cases",
    "new_cases",
    "total_deaths",
    "new_deaths",
    "code",
    "continent",
    "population",
]

CHUNK_SIZE = 50_000
DOWNLOAD_TIMEOUT_SECONDS = 120
USER_AGENT = "covid-data-pipeline-student/0.1 (phase-2-exploration)"

# Compact.csv has no recovered/active/state columns. These names are checked
# against the real header so the report does not rely on memory.
ABSENT_COLUMNS_TO_CONFIRM = [
    "recovered",
    "total_recovered",
    "active",
    "active_cases",
    "state",
    "province",
    "latitude",
    "longitude",
    "lat",
    "long",
]


def download_source(url: str, destination: Path, force: bool = False) -> Path:
    """Stream the CSV to disk so a 180 MB file does not sit fully in RAM."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0 and not force:
        logger.info("Using cached file: %s (%s bytes)", destination, destination.stat().st_size)
        return destination

    logger.info("Starting download from %s", url)
    with requests.get(
        url,
        stream=True,
        timeout=DOWNLOAD_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    ) as response:
        response.raise_for_status()
        bytes_written = 0
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                handle.write(chunk)
                bytes_written += len(chunk)
                if bytes_written % (20 * 1024 * 1024) < 1024 * 256:
                    logger.info("Downloaded %s MB so far", bytes_written // (1024 * 1024))

    logger.info("Download complete: %s bytes", destination.stat().st_size)
    return destination


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_header(path: Path) -> list[str]:
    return pd.read_csv(path, nrows=0).columns.tolist()


def _safe_min(current: Any, value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return current
    if current is None:
        return value
    return min(current, value)


def _safe_max(current: Any, value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return current
    if current is None:
        return value
    return max(current, value)


def profile_csv(path: Path) -> dict[str, Any]:
    """Walk the file in chunks and collect quality statistics.

    Chunking keeps memory stable on a laptop. The CSV is sorted by country
    then date, so we can compare each row to the previous day by carrying
    one leftover row between chunks.
    """
    header = read_header(path)
    missing_expected = [col for col in PROFILE_COLUMNS if col not in header]
    if missing_expected:
        raise ValueError(f"Source header is missing expected columns: {missing_expected}")

    confirmed_absent = [col for col in ABSENT_COLUMNS_TO_CONFIRM if col not in header]

    row_count = 0
    null_counts: Counter[str] = Counter()
    country_counter: Counter[str] = Counter()
    location_meta: dict[str, dict[str, Any]] = {}
    duplicate_preview: list[str] = []
    seen_keys: set[tuple[str, str]] | None = set()
    # Full pairwise uniqueness on ~400k rows is fine in memory as tuples.
    duplicate_count = 0
    negative_new_cases = 0
    negative_new_deaths = 0
    negative_total_cases = 0
    negative_total_deaths = 0
    new_cases_mismatch = 0
    new_deaths_mismatch = 0
    min_date = None
    max_date = None
    previous_row: dict[str, Any] | None = None

    logger.info("Profiling %s in chunks of %s", path.name, CHUNK_SIZE)
    for chunk in pd.read_csv(
        path,
        usecols=PROFILE_COLUMNS,
        chunksize=CHUNK_SIZE,
        dtype={"country": "string", "code": "string", "continent": "string"},
        parse_dates=["date"],
    ):
        row_count += len(chunk)
        for column in PROFILE_COLUMNS:
            null_counts[column] += int(chunk[column].isna().sum())

        country_counter.update(chunk["country"].dropna().astype(str).tolist())

        grouped = (
            chunk.groupby(["country", "code", "continent"], dropna=False)
            .size()
            .reset_index(name="n")
        )
        for record in grouped.to_dict(orient="records"):
            name = str(record["country"])
            meta = location_meta.setdefault(
                name,
                {
                    "codes": set(),
                    "continents": set(),
                    "row_count": 0,
                },
            )
            if pd.notna(record["code"]):
                meta["codes"].add(str(record["code"]))
            if pd.notna(record["continent"]):
                meta["continents"].add(str(record["continent"]))
            else:
                meta["continents"].add("")
            meta["row_count"] += int(record["n"])

        min_date = _safe_min(min_date, chunk["date"].min())
        max_date = _safe_max(max_date, chunk["date"].max())

        keys = list(zip(chunk["country"].astype(str), chunk["date"].astype(str)))
        for key in keys:
            if key in seen_keys:
                duplicate_count += 1
                if len(duplicate_preview) < 10:
                    duplicate_preview.append(f"{key[0]}|{key[1]}")
            else:
                seen_keys.add(key)

        negative_new_cases += int((chunk["new_cases"] < 0).sum())
        negative_new_deaths += int((chunk["new_deaths"] < 0).sum())
        negative_total_cases += int((chunk["total_cases"] < 0).sum())
        negative_total_deaths += int((chunk["total_deaths"] < 0).sum())

        ordered = chunk.sort_values(["country", "date"]).reset_index(drop=True)
        if previous_row is not None:
            ordered = pd.concat([previous_row, ordered], ignore_index=True)

        lagged_cases = ordered.groupby("country", sort=False)["total_cases"].shift(1)
        lagged_deaths = ordered.groupby("country", sort=False)["total_deaths"].shift(1)
        same_country_lag = ordered["country"].eq(ordered.groupby("country", sort=False)["country"].shift(1))

        case_diff = ordered["total_cases"] - lagged_cases
        death_diff = ordered["total_deaths"] - lagged_deaths
        comparable_cases = (
            same_country_lag
            & lagged_cases.notna()
            & ordered["total_cases"].notna()
            & ordered["new_cases"].notna()
        )
        comparable_deaths = (
            same_country_lag
            & lagged_deaths.notna()
            & ordered["total_deaths"].notna()
            & ordered["new_deaths"].notna()
        )
        new_cases_mismatch += int(
            (comparable_cases & ((case_diff - ordered["new_cases"]).abs() > 0.5)).sum()
        )
        new_deaths_mismatch += int(
            (comparable_deaths & ((death_diff - ordered["new_deaths"]).abs() > 0.5)).sum()
        )
        previous_row = ordered.tail(1)

        logger.info("Processed %s rows", f"{row_count:,}")

    locations_without_continent = sorted(
        name
        for name, meta in location_meta.items()
        if meta["continents"] == {""} or meta["continents"] == set()
    )
    multi_code_locations = {
        name: sorted(meta["codes"])
        for name, meta in location_meta.items()
        if len(meta["codes"]) > 1
    }
    location_details = [
        {
            "location": name,
            "codes": sorted(meta["codes"]),
            "continents": sorted(value for value in meta["continents"] if value),
            "has_continent": any(meta["continents"] - {""}),
            "row_count": meta["row_count"],
        }
        for name, meta in sorted(location_meta.items())
    ]

    profile = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": OWID_COVID_URL,
        "local_file": str(path),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "column_count": len(header),
        "columns": header,
        "confirmed_absent_columns": confirmed_absent,
        "row_count": row_count,
        "min_date": None if min_date is None else pd.Timestamp(min_date).date().isoformat(),
        "max_date": None if max_date is None else pd.Timestamp(max_date).date().isoformat(),
        "unique_location_count": len(location_meta),
        "null_counts": dict(null_counts),
        "null_rates_percent": {
            column: round(100 * null_counts[column] / row_count, 3) if row_count else None
            for column in PROFILE_COLUMNS
        },
        "duplicate_country_date_count": duplicate_count,
        "duplicate_preview": duplicate_preview,
        "negative_new_cases": negative_new_cases,
        "negative_new_deaths": negative_new_deaths,
        "negative_total_cases": negative_total_cases,
        "negative_total_deaths": negative_total_deaths,
        "new_cases_differs_from_cumulative_lag": new_cases_mismatch,
        "new_deaths_differs_from_cumulative_lag": new_deaths_mismatch,
        "locations_without_continent": locations_without_continent,
        "locations_with_multiple_codes": multi_code_locations,
        "location_details": location_details,
        "top_locations_by_rows": country_counter.most_common(15),
        "grain": "One source row = one OWID location name + one date",
        "business_key": ["country", "date"],
    }
    return profile


def write_outputs(profile: dict[str, Any]) -> tuple[Path, Path]:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = PROCESSED_DATA_DIR / "source_profile.json"
    csv_path = PROCESSED_DATA_DIR / "source_locations.csv"

    json_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    pd.DataFrame(profile["location_details"]).to_csv(csv_path, index=False)

    logger.info("Wrote profile JSON to %s", json_path)
    return json_path, csv_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile the OWID compact COVID CSV.")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Download again even if a local CSV already exists.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Profile an existing local file only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    local_csv = RAW_DATA_DIR / RAW_CSV_NAME

    logger.info("Starting source exploration")
    if args.skip_download:
        if not local_csv.exists():
            raise FileNotFoundError(f"No local file at {local_csv}")
    else:
        download_source(OWID_COVID_URL, local_csv, force=args.force_download)

    profile = profile_csv(local_csv)
    write_outputs(profile)
    logger.info(
        "Raw records: %s | locations: %s | date range: %s to %s",
        f"{profile['row_count']:,}",
        profile["unique_location_count"],
        profile["min_date"],
        profile["max_date"],
    )
    logger.info("Duplicate (country, date) rows: %s", profile["duplicate_country_date_count"])
    logger.info("Locations without continent: %s", profile["locations_without_continent"])
    logger.info("Pipeline exploration completed successfully")


if __name__ == "__main__":
    main()
