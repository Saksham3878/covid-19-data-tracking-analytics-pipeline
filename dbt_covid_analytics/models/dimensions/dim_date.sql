{{ config(
    materialized='table'
) }}

SELECT
    ROW_NUMBER() OVER (ORDER BY date) AS date_id,
    date AS full_date,
    EXTRACT(YEAR FROM date)::INT AS year,
    EXTRACT(MONTH FROM date)::INT AS month,
    TO_CHAR(date, 'Month') AS month_name,
    EXTRACT(QUARTER FROM date)::INT AS quarter,
    EXTRACT(DAY FROM date)::INT AS day,
    TO_CHAR(date, 'Day') AS day_name

FROM (
    SELECT DISTINCT
        date
    FROM {{ ref('stg_covid') }}
    WHERE date IS NOT NULL
) dates