"""Load settings from environment variables.

Credentials never belong in source code. Phase 2 only needs the public
dataset URL and local folder paths.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

OWID_COVID_URL = os.getenv(
    "OWID_COVID_URL",
    "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv",
)
RAW_DATA_DIR = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
PROCESSED_DATA_DIR = PROJECT_ROOT / os.getenv("PROCESSED_DATA_DIR", "data/processed")
RAW_CSV_NAME = "owid_covid_compact.csv"
