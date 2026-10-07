"""Tests that do not require the 180 MB source download."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.exploration.profile_source import ABSENT_COLUMNS_TO_CONFIRM, read_header


def test_read_header_returns_column_names(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("country,date,total_cases\nIndia,2020-01-01,0\n", encoding="utf-8")
    assert read_header(csv_path) == ["country", "date", "total_cases"]


def test_recovered_and_state_are_treated_as_absent() -> None:
    header = ["country", "date", "total_cases", "new_cases", "code"]
    confirmed_absent = [col for col in ABSENT_COLUMNS_TO_CONFIRM if col not in header]
    assert "recovered" in confirmed_absent
    assert "state" in confirmed_absent
    assert "active_cases" in confirmed_absent


def test_duplicate_business_key_detection() -> None:
    frame = pd.DataFrame(
        {
            "country": ["India", "India", "India"],
            "date": ["2020-03-01", "2020-03-01", "2020-03-02"],
        }
    )
    duplicated = frame.duplicated(subset=["country", "date"], keep="first").sum()
    assert int(duplicated) == 1
