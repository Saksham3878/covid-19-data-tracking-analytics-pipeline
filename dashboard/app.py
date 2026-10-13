import os
from pathlib import Path

import pandas as pd
import psycopg2
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="COVID-19 Data Analytics",
    page_icon="🦠",
    layout="wide"
)


# =========================================================
# ENVIRONMENT
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")


# =========================================================
# DATABASE CONNECTION
# =========================================================


def get_setting(key):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)


def get_connection():
    return psycopg2.connect(
        host=get_setting("POSTGRES_HOST"),
        port=get_setting("POSTGRES_PORT"),
        database=get_setting("POSTGRES_DB"),
        user=get_setting("POSTGRES_USER"),
        password=get_setting("POSTGRES_PASSWORD"),
        sslmode=get_setting("POSTGRES_SSLMODE") or "prefer"
    )


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    conn = get_connection()

    try:

        global_data = pd.read_sql_query(
            """
            SELECT *
            FROM analytics.global_daily
            ORDER BY full_date
            """,
            conn
        )

        country_data = pd.read_sql_query(
            """
            SELECT *
            FROM analytics.dashboard_country_summary
            ORDER BY total_cases DESC
            """,
            conn
        )

        india_data = pd.read_sql_query(
            """
            SELECT *
            FROM analytics.india_analysis
            ORDER BY full_date
            """,
            conn
        )

        monthly_data = pd.read_sql_query(
            """
            SELECT *
            FROM analytics.country_monthly_trend
            ORDER BY country_name, year, month
            """,
            conn
        )

        return (
            global_data,
            country_data,
            india_data,
            monthly_data
        )

    finally:
        conn.close()


# =========================================================
# HEADER
# =========================================================

st.title("🦠 COVID-19 Data Tracking & Analytics")

st.markdown(
    """
    **End-to-End Data Engineering Dashboard**

    Data pipeline: **OWID → Python → PostgreSQL → dbt → Airflow → Streamlit**
    """
)

st.divider()


# =========================================================
# LOAD DATA
# =========================================================

try:

    (
        global_data,
        country_data,
        india_data,
        monthly_data
    ) = load_data()

except Exception as e:

    st.error("Database connection failed.")
    st.code(str(e))

    st.stop()


# =========================================================
# DATA PREPARATION
# =========================================================

global_data["full_date"] = pd.to_datetime(global_data["full_date"])
india_data["full_date"] = pd.to_datetime(india_data["full_date"])

monthly_data["month_start"] = pd.to_datetime(
    monthly_data["month_start"]
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Dashboard Controls")

# Country selector
countries = sorted(
    country_data["country_name"].dropna().unique()
)

selected_country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=(
        countries.index("India")
        if "India" in countries
        else 0
    )
)

# Top N
top_n = st.sidebar.slider(
    "Top Countries",
    min_value=5,
    max_value=20,
    value=10
)

# Date range
min_date = global_data["full_date"].min().date()
max_date = global_data["full_date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

st.sidebar.divider()

st.sidebar.info(
    """
    **Data Source**

    Our World in Data (OWID)

    **Warehouse**

    PostgreSQL + dbt

    **Orchestration**

    Apache Airflow
    """
)


# =========================================================
# FILTER GLOBAL DATA
# =========================================================

if isinstance(date_range, tuple) and len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])

    filtered_global = global_data[
        (global_data["full_date"] >= start_date)
        &
        (global_data["full_date"] <= end_date)
    ].copy()

else:

    filtered_global = global_data.copy()


# =========================================================
# GLOBAL KPIs
# =========================================================

latest_global = global_data.iloc[-1]

latest_date = latest_global["full_date"]

total_cases = latest_global["total_cases"]
total_deaths = latest_global["total_deaths"]

latest_new_cases = latest_global["new_cases"]
latest_new_deaths = latest_global["new_deaths"]


st.subheader("🌍 Global Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Total Cases",
        f"{total_cases:,.0f}"
    )

with col2:

    st.metric(
        "Total Deaths",
        f"{total_deaths:,.0f}"
    )

with col3:

    st.metric(
        "Latest New Cases",
        f"{latest_new_cases:,.0f}"
    )

with col4:

    st.metric(
        "Latest New Deaths",
        f"{latest_new_deaths:,.0f}"
    )

st.caption(
    f"Latest available global data: {latest_date.strftime('%d %B %Y')}"
)


# =========================================================
# GLOBAL CUMULATIVE TRENDS
# =========================================================

st.subheader("📈 Global COVID-19 Trends")

col1, col2 = st.columns(2)

with col1:

    fig_cases = px.line(
        filtered_global,
        x="full_date",
        y="total_cases",
        title="Cumulative COVID-19 Cases",
        labels={
            "full_date": "Date",
            "total_cases": "Cases"
        }
    )

    fig_cases.update_layout(
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_cases,
        use_container_width=True
    )


with col2:

    fig_deaths = px.line(
        filtered_global,
        x="full_date",
        y="total_deaths",
        title="Cumulative COVID-19 Deaths",
        labels={
            "full_date": "Date",
            "total_deaths": "Deaths"
        }
    )

    fig_deaths.update_layout(
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_deaths,
        use_container_width=True
    )


# =========================================================
# DAILY CASES / DEATHS
# =========================================================

col1, col2 = st.columns(2)

with col1:

    fig_daily_cases = px.bar(
        filtered_global,
        x="full_date",
        y="new_cases",
        title="Daily New Cases",
        labels={
            "full_date": "Date",
            "new_cases": "New Cases"
        }
    )

    st.plotly_chart(
        fig_daily_cases,
        use_container_width=True
    )


with col2:

    fig_daily_deaths = px.bar(
        filtered_global,
        x="full_date",
        y="new_deaths",
        title="Daily New Deaths",
        labels={
            "full_date": "Date",
            "new_deaths": "New Deaths"
        }
    )

    st.plotly_chart(
        fig_daily_deaths,
        use_container_width=True
    )


# =========================================================
# COUNTRY COMPARISON
# =========================================================

st.divider()

st.subheader("🌎 Country Comparison")

top_countries = country_data.head(top_n).copy()

col1, col2 = st.columns(2)

with col1:

    fig_country_cases = px.bar(
        top_countries,
        x="country_name",
        y="total_cases",
        title=f"Top {top_n} Countries by Total Cases",
        labels={
            "country_name": "Country",
            "total_cases": "Total Cases"
        }
    )

    fig_country_cases.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_country_cases,
        use_container_width=True
    )


with col2:

    death_rate_data = country_data.head(top_n).copy()

    fig_death_rate = px.bar(
        death_rate_data,
        x="country_name",
        y="death_rate_percent",
        title=f"Death Rate Comparison — Top {top_n}",
        labels={
            "country_name": "Country",
            "death_rate_percent": "Death Rate (%)"
        }
    )

    fig_death_rate.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_death_rate,
        use_container_width=True
    )


# =========================================================
# SELECTED COUNTRY
# =========================================================

st.divider()

st.subheader(f"📊 {selected_country} Analysis")

selected_summary = country_data[
    country_data["country_name"] == selected_country
]

if not selected_summary.empty:

    selected_summary = selected_summary.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Cases",
            f"{selected_summary['total_cases']:,.0f}"
        )

    with col2:

        st.metric(
            "Total Deaths",
            f"{selected_summary['total_deaths']:,.0f}"
        )

    with col3:

        st.metric(
            "Population",
            (
                f"{selected_summary['population']:,.0f}"
                if pd.notna(selected_summary["population"])
                else "N/A"
            )
        )

    with col4:

        st.metric(
            "Death Rate",
            f"{selected_summary['death_rate_percent']:.2f}%"
        )


# =========================================================
# COUNTRY MONTHLY TREND
# =========================================================

selected_monthly = monthly_data[
    monthly_data["country_name"] == selected_country
].copy()

if not selected_monthly.empty:

    st.subheader(
        f"📅 Monthly COVID-19 Trend — {selected_country}"
    )

    col1, col2 = st.columns(2)

    with col1:

        fig_month_cases = px.line(
            selected_monthly,
            x="month_start",
            y="monthly_cases",
            title="Monthly Cases",
            labels={
                "month_start": "Month",
                "monthly_cases": "Cases"
            }
        )

        st.plotly_chart(
            fig_month_cases,
            use_container_width=True
        )

    with col2:

        fig_month_deaths = px.line(
            selected_monthly,
            x="month_start",
            y="monthly_deaths",
            title="Monthly Deaths",
            labels={
                "month_start": "Month",
                "monthly_deaths": "Deaths"
            }
        )

        st.plotly_chart(
            fig_month_deaths,
            use_container_width=True
        )


# =========================================================
# INDIA ANALYSIS
# =========================================================

st.divider()

st.subheader("🇮🇳 India Analysis")

india_filtered = india_data.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:

    india_filtered = india_data[
        (india_data["full_date"] >= start_date)
        &
        (india_data["full_date"] <= end_date)
    ].copy()


india_latest = india_data.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "India Total Cases",
        f"{india_latest['total_cases']:,.0f}"
    )

with col2:

    st.metric(
        "India Total Deaths",
        f"{india_latest['total_deaths']:,.0f}"
    )

with col3:

    st.metric(
        "Latest New Cases",
        f"{india_latest['new_cases']:,.0f}"
    )

with col4:

    st.metric(
        "Latest New Deaths",
        f"{india_latest['new_deaths']:,.0f}"
    )


col1, col2 = st.columns(2)

with col1:

    fig_india_cases = px.line(
        india_filtered,
        x="full_date",
        y="total_cases",
        title="India Cumulative Cases",
        labels={
            "full_date": "Date",
            "total_cases": "Cases"
        }
    )

    st.plotly_chart(
        fig_india_cases,
        use_container_width=True
    )


with col2:

    fig_india_deaths = px.line(
        india_filtered,
        x="full_date",
        y="total_deaths",
        title="India Cumulative Deaths",
        labels={
            "full_date": "Date",
            "total_deaths": "Deaths"
        }
    )

    st.plotly_chart(
        fig_india_deaths,
        use_container_width=True
    )


# =========================================================
# COUNTRY DATA TABLE
# =========================================================

st.divider()

st.subheader("📋 Country Data")

display_columns = [
    "country_name",
    "total_cases",
    "total_deaths",
    "population",
    "reporting_days",
    "death_rate_percent"
]

display_data = country_data[display_columns].copy()

display_data.columns = [
    "Country",
    "Total Cases",
    "Total Deaths",
    "Population",
    "Reporting Days",
    "Death Rate (%)"
]

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# DOWNLOAD DATA
# =========================================================

st.subheader("⬇️ Download Data")

col1, col2 = st.columns(2)

with col1:

    country_csv = country_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Country Data",
        data=country_csv,
        file_name="covid_country_data.csv",
        mime="text/csv"
    )


with col2:

    global_csv = global_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Global Data",
        data=global_csv,
        file_name="covid_global_data.csv",
        mime="text/csv"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    ### 🔧 Data Engineering Pipeline

    **Source:** Our World in Data  
    **Processing:** Python + Pandas  
    **Database:** PostgreSQL  
    **Transformation:** dbt  
    **Orchestration:** Apache Airflow  
    **Visualization:** Streamlit + Plotly

    ---
    
    *COVID-19 Data Tracking & Analytics Pipeline*
    """
)