import pandas as pd
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "covid_cleaned.csv"
)


def validate_covid_data():
    """
    Validate the cleaned COVID-19 dataset.
    """

    print("Loading cleaned COVID-19 dataset...")

    df = pd.read_csv(PROCESSED_FILE)

    errors = []

    # --------------------------------------------------
    # 1. Check required columns
    # --------------------------------------------------

    required_columns = [
        "country",
        "date",
        "total_cases",
        "new_cases",
        "total_deaths",
        "new_deaths",
        "population"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing columns: {missing_columns}"
        )

    # --------------------------------------------------
    # 2. Check missing country values
    # --------------------------------------------------

    missing_country = df["country"].isna().sum()

    if missing_country > 0:
        errors.append(
            f"Missing country values: {missing_country}"
        )

    # --------------------------------------------------
    # 3. Check invalid dates
    # --------------------------------------------------

    dates = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_dates = dates.isna().sum()

    if invalid_dates > 0:
        errors.append(
            f"Invalid dates: {invalid_dates}"
        )

    # --------------------------------------------------
    # 4. Check duplicate country-date records
    # --------------------------------------------------

    duplicates = df.duplicated(
        subset=["country", "date"]
    ).sum()

    if duplicates > 0:
        errors.append(
            f"Duplicate country-date records: {duplicates}"
        )

    # --------------------------------------------------
    # 5. Check negative cases
    # --------------------------------------------------

    negative_cases = (
        (df["new_cases"] < 0)
        .sum()
    )

    if negative_cases > 0:
        errors.append(
            f"Negative new_cases values: {negative_cases}"
        )

    # --------------------------------------------------
    # 6. Check negative deaths
    # --------------------------------------------------

    negative_deaths = (
        (df["new_deaths"] < 0)
        .sum()
    )

    if negative_deaths > 0:
        errors.append(
            f"Negative new_deaths values: {negative_deaths}"
        )

    # --------------------------------------------------
    # 7. Display validation result
    # --------------------------------------------------

    print("\n========== VALIDATION RESULT ==========")

    if errors:
        print("VALIDATION FAILED")

        for error in errors:
            print(f"- {error}")

        return False

    print("VALIDATION PASSED")
    print(f"Rows checked: {len(df)}")
    print(f"Columns checked: {len(df.columns)}")
    print("Country-date duplicates: 0")
    print("Invalid dates: 0")
    print("Negative new cases: 0")
    print("Negative new deaths: 0")

    return True


if __name__ == "__main__":
    validate_covid_data()