{{ config(
    materialized='table'
) }}

SELECT
    c.country_id,
    d.date_id,

    CASE
        WHEN s.total_cases::text = 'NaN' THEN NULL
        ELSE s.total_cases
    END AS total_cases,

    CASE
        WHEN s.new_cases::text = 'NaN' THEN NULL
        ELSE s.new_cases
    END AS new_cases,

    CASE
        WHEN s.total_deaths::text = 'NaN' THEN NULL
        ELSE s.total_deaths
    END AS total_deaths,

    CASE
        WHEN s.new_deaths::text = 'NaN' THEN NULL
        ELSE s.new_deaths
    END AS new_deaths,

    CASE
        WHEN s.population::text = 'NaN' THEN NULL
        ELSE s.population
    END AS population

FROM {{ ref('stg_covid') }} s

JOIN {{ ref('dim_country') }} c
    ON s.country = c.country_name

JOIN {{ ref('dim_date') }} d
    ON s.date = d.full_date