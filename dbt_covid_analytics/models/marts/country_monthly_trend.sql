{{ config(
    materialized='table'
) }}

SELECT
    c.country_id,
    c.country_name,

    d.year,
    d.month,

    MIN(d.full_date) AS month_start,

    SUM(COALESCE(f.new_cases, 0)) AS monthly_cases,
    SUM(COALESCE(f.new_deaths, 0)) AS monthly_deaths,

    MAX(f.total_cases) AS cumulative_cases,
    MAX(f.total_deaths) AS cumulative_deaths

FROM {{ ref('fact_covid') }} f

JOIN {{ ref('dim_country') }} c
    ON f.country_id = c.country_id

JOIN {{ ref('dim_date') }} d
    ON f.date_id = d.date_id

GROUP BY
    c.country_id,
    c.country_name,
    d.year,
    d.month

ORDER BY
    c.country_name,
    d.year,
    d.month