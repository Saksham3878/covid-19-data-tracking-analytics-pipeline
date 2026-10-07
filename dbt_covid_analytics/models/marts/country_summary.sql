{{ config(
    materialized='table'
) }}

SELECT
    c.country_id,
    c.country_name,

    SUM(COALESCE(f.new_cases, 0)) AS total_cases,
    SUM(COALESCE(f.new_deaths, 0)) AS total_deaths,

    MAX(f.population) AS population,

    COUNT(DISTINCT f.date_id) AS reporting_days,

    CASE
        WHEN SUM(COALESCE(f.new_cases, 0)) > 0
        THEN
            ROUND(
                (
                    SUM(COALESCE(f.new_deaths, 0))
                    / SUM(COALESCE(f.new_cases, 0))
                ) * 100,
                2
            )
        ELSE 0
    END AS death_rate_percent

FROM {{ ref('fact_covid') }} f

JOIN {{ ref('dim_country') }} c
    ON f.country_id = c.country_id

GROUP BY
    c.country_id,
    c.country_name

ORDER BY
    total_cases DESC