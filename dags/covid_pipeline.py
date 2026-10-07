from airflow.sdk import dag, task
from datetime import datetime
import subprocess


@dag(
    dag_id="covid_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
)
def covid_pipeline():

    @task
    def run_ingestion():
        subprocess.run(
            ["python", "src/ingestion/ingest_covid.py"],
            check=True
        )

        print("COVID data ingestion completed successfully!")

    @task
    def run_cleaning():
        subprocess.run(
            ["python", "src/transformation/clean_covid.py"],
            check=True
        )

        print("COVID data cleaning completed successfully!")

    @task
    def run_postgres_load():
        subprocess.run(
            ["python", "src/ingestion/load_to_postgres.py"],
            check=True
        )

        print("COVID data loaded into PostgreSQL successfully!")

    @task
    def run_dbt():
        subprocess.run(
            [
                "dbt",
                "build",
                "--project-dir",
                "/opt/airflow/dbt_covid_analytics",
                "--profiles-dir",
                "/opt/airflow/dbt_profiles"
            ],
            check=True
        )

        print("dbt build completed successfully!")

    ingestion = run_ingestion()
    cleaning = run_cleaning()
    postgres_load = run_postgres_load()
    dbt = run_dbt()

    ingestion >> cleaning >> postgres_load >> dbt


covid_pipeline()