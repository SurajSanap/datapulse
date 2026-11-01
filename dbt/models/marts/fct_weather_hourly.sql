{{ config(materialized='table') }}

with ranked_forecasts as (
    select
        observation_id,
        latitude,
        longitude,
        observed_at_utc,
        temperature_c,
        relative_humidity_pct,
        precipitation_mm,
        wind_speed_kmh,
        ingested_at,
        row_number() over (
            partition by latitude, longitude, observed_at_utc
            order by ingested_at desc, observation_id desc
        ) as snapshot_rank
    from {{ ref('stg_weather_observations') }}
)

select
    observation_id as source_observation_id,
    latitude,
    longitude,
    observed_at_utc,
    temperature_c,
    relative_humidity_pct,
    precipitation_mm,
    wind_speed_kmh,
    ingested_at
from ranked_forecasts
where snapshot_rank = 1
