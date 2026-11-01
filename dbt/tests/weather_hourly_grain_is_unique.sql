select
    latitude,
    longitude,
    observed_at_utc
from {{ ref('fct_weather_hourly') }}
group by latitude, longitude, observed_at_utc
having count(*) > 1
