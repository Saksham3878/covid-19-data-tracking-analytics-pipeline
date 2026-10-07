import pandas as pd
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# File locations
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_FILE = RAW_DIR / "owid_covid_compact.csv"


def load_covid_data():
    """
    Load the raw COVID-19 dataset.
    """

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"COVID dataset not found: {RAW_FILE}"
        )

    print("Loading COVID-19 dataset...")

    df = pd.read_csv(RAW_FILE)

    print(f"Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


if __name__ == "__main__":
    df = load_covid_data()

    print("\nFirst 5 rows:")
    print(df.head())