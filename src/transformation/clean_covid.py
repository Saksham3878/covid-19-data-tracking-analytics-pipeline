import pandas as pd
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Input and output paths
RAW_FILE = BASE_DIR / "data" / "raw" / "owid_covid_compact.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "covid_cleaned.csv"


def clean_covid_data():

    print("Reading raw COVID-19 dataset...")

    # Only load the columns required for the pipeline
    required_columns = [
        "country",
        "date",
        "total_cases",
        "new_cases",
        "total_deaths",
        "new_deaths",
        "population"
    ]

    df = pd.read_csv(
        RAW_FILE,
        usecols=required_columns
    )

    print(f"Original rows: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    # --------------------------------------------------
    # 1. Convert date column
    # --------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    # --------------------------------------------------
    # 2. Standardize country names
    # --------------------------------------------------

    df["country"] = (
        df["country"]
        .astype(str)
        .str.strip()
    )

    df = df[df["country"] != ""]

    # --------------------------------------------------
    # 3. Remove duplicate country-date records
    # --------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["country", "date"],
        keep="last"
    )

    after_duplicates = len(df)

    print(
        f"Duplicates removed: "
        f"{before_duplicates - after_duplicates}"
    )

    # --------------------------------------------------
    # 4. Convert numeric columns
    # --------------------------------------------------

    numeric_columns = [
        "total_cases",
        "new_cases",
        "total_deaths",
        "new_deaths",
        "population"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------
    # 5. Replace negative case/death values
    # --------------------------------------------------

    df.loc[df["new_cases"] < 0, "new_cases"] = 0
    df.loc[df["new_deaths"] < 0, "new_deaths"] = 0

    # --------------------------------------------------
    # 6. Sort data
    # --------------------------------------------------

    df = df.sort_values(
        by=["country", "date"]
    ).reset_index(drop=True)

    # --------------------------------------------------
    # 7. Create processed directory
    # --------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 8. Save cleaned dataset
    # --------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nCleaning completed successfully.")
    print(f"Final rows: {len(df)}")
    print(f"Final columns: {len(df.columns)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    clean_covid_data()