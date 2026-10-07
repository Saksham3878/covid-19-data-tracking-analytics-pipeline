import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

CSV_FILE = BASE_DIR / "data" / "processed" / "covid_cleaned.csv"


conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)


cursor = conn.cursor()

print("Clearing raw COVID table...")
cursor.execute("TRUNCATE TABLE raw.covid_raw;")

print("Loading COVID data using PostgreSQL COPY...")

with open(CSV_FILE, "r", encoding="utf-8") as file:
    cursor.copy_expert(
        """
        COPY raw.covid_raw
        (
            country,
            date,
            total_cases,
            new_cases,
            total_deaths,
            new_deaths,
            population
        )
        FROM STDIN
        WITH CSV HEADER
        """,
        file
    )

conn.commit()

cursor.close()
conn.close()

print("COVID data successfully loaded into PostgreSQL.")
