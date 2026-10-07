{{ config(
    materialized='view'
) }}

SELECT
    country,
    date,
    total_cases,
    new_cases,
    total_deaths,
    new_deaths,
    population

FROM {{ source('raw', 'covid_raw') }}