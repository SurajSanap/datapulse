select observation_id
from {{ ref('stg_weather_observations') }}
where (relative_humidity_pct is not null and relative_humidity_pct not between 0 and 100)
   or (precipitation_mm is not null and precipitation_mm < 0)
   or (wind_speed_kmh is not null and wind_speed_kmh < 0)
