{{ config(
    materialized='table'
) }}

SELECT
    d.full_date,

    SUM(COALESCE(f.total_cases, 0)) AS total_cases,
    SUM(COALESCE(f.new_cases, 0)) AS new_cases,
    SUM(COALESCE(f.total_deaths, 0)) AS total_deaths,
    SUM(COALESCE(f.new_deaths, 0)) AS new_deaths

FROM {{ ref('fact_covid') }} f

JOIN {{ ref('dim_date') }} d
    ON f.date_id = d.date_id

GROUP BY
    d.full_date

ORDER BY
    d.full_date