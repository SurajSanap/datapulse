{{ config(materialized='view') }}

select
    cast(id as integer) as observation_id,
    cast(latitude as double precision) as latitude,
    cast(longitude as double precision) as longitude,
    cast(observed_at as timestamp with time zone) as observed_at_utc,
    cast(temperature_c as double precision) as temperature_c,
    cast(relative_humidity_pct as integer) as relative_humidity_pct,
    cast(precipitation_mm as double precision) as precipitation_mm,
    cast(wind_speed_kmh as double precision) as wind_speed_kmh,
    raw_payload,
    cast(created_at as timestamp with time zone) as ingested_at
from {{ source('weather', 'weather_observations') }}
