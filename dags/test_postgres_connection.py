from airflow.sdk import dag, task
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="test_postgres_connection",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
)
def test_postgres_connection():

    @task
    def test_connection():
        hook = PostgresHook(postgres_conn_id="covid_postgres")

        result = hook.get_first(
            "SELECT current_database();"
        )

        print("Connected database:", result[0])

    test_connection()


test_postgres_connection()