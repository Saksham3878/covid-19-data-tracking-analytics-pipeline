{{ config(
    materialized='table'
) }}

SELECT
    d.full_date,

    f.total_cases,
    f.new_cases,
    f.total_deaths,
    f.new_deaths,
    f.population

FROM {{ ref('fact_covid') }} f

JOIN {{ ref('dim_country') }} c
    ON f.country_id = c.country_id

JOIN {{ ref('dim_date') }} d
    ON f.date_id = d.date_id

WHERE LOWER(c.country_name) = 'india'

ORDER BY
    d.full_date