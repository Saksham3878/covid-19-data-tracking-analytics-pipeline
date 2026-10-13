# COVID-19 Data Tracking & Analytics Pipeline

An end-to-end data engineering project that processes public COVID-19 data, transforms it into analytics-ready datasets, and presents public-health trends through an interactive dashboard.

**Live Dashboard:** [Open Dashboard](https://covid-19-data-tracking-analytics-pipeline-hcty5u39qbeyrgrwymu9.streamlit.app/)

**GitHub Repository:** [View Source Code](https://github.com/Saksham3878/covid-19-data-tracking-analytics-pipeline)

## Project Overview

This project demonstrates a data engineering workflow using publicly available COVID-19 data. It covers data ingestion, cleaning, validation, database loading, dimensional modeling, orchestration, and interactive visualization.

The pipeline uses Python and Pandas for data processing, PostgreSQL for storage, dbt for transformations and testing, Apache Airflow for orchestration, and Streamlit with Plotly for visualization.

## Architecture

```text
Our World in Data (OWID)
          |
          v
Python Data Ingestion
          |
          v
Data Cleaning & Validation
          |
          v
      PostgreSQL
          |
          v
   dbt Transformations
          |
          v
Analytics Tables & Models
          |
          v
 Streamlit + Plotly Dashboard
```

Apache Airflow orchestrates the ingestion, cleaning, database loading, and dbt transformation tasks.

## Technology Stack

* **Programming:** Python
* **Data Processing:** Pandas, NumPy
* **Database:** PostgreSQL
* **Data Transformation:** dbt Core, SQL
* **Workflow Orchestration:** Apache Airflow
* **Containerization:** Docker, Docker Compose
* **Dashboard:** Streamlit, Plotly
* **Data Source:** Our World in Data COVID-19 dataset
* **Version Control:** Git, GitHub

## Key Features

* Ingests publicly available COVID-19 data.
* Cleans and validates data before database loading.
* Handles duplicate records, invalid dates, and negative case/death values.
* Stores data in PostgreSQL.
* Uses dbt models and tests to build analytics-ready datasets.
* Organizes data using dimensional modeling concepts.
* Orchestrates pipeline tasks through an Airflow DAG.
* Provides an interactive dashboard with country and date filters.
* Visualizes global trends, country comparisons, and India-specific trends.
* Supports downloading dashboard data as CSV.

## Analytics

The dashboard includes:

* Global COVID-19 case and death trends.
* Country-level comparisons and summary statistics.
* Monthly trends across countries.
* India-specific daily trends.
* Historical analysis using the available dataset.

## Data Source

The project uses the public [Our World in Data COVID-19 dataset](https://github.com/owid/covid-19-data).

The data represents the latest available records in the downloaded dataset, not a guaranteed real-time feed.

## Project Structure

```text
Covid 19 Data Tracking/
├── dags/
│   └── covid_pipeline.py
├── dashboard/
│   └── app.py
├── dbt_covid_analytics/
│   ├── models/
│   └── tests/
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── ingestion/
│   ├── transformation/
│   └── validation/
├── tests/
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## Running the Dashboard Locally

### 1. Clone the repository

```bash
git clone https://github.com/Saksham3878/covid-19-data-tracking-analytics-pipeline.git
cd covid-19-data-tracking-analytics-pipeline
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database credentials

Create a local `.env` file using `.env.example` as a template. Set the PostgreSQL host, port, database name, username, and password.

Never commit real passwords, API keys, or database connection strings.

### 5. Start the dashboard

```bash
streamlit run dashboard/app.py
```

Open the local URL displayed in the terminal.

## Future Improvements

* Schedule and monitor automated refreshes in a hosted environment.
* Add data freshness indicators and pipeline failure alerts.
* Expand data-quality monitoring and test coverage.
* Improve deployment automation and infrastructure configuration.

## Author

**Saksham Sharma**

B.Tech Computer Science Engineering

GitHub: [Saksham3878](https://github.com/Saksham3878)
