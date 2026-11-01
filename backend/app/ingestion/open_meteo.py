"""Open-Meteo hourly forecast fetching and response validation."""

from datetime import datetime, timezone
from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
)


class OpenMeteoError(ValueError):
    """Raised when Open-Meteo returns an invalid or incomplete response."""


def fetch_hourly_weather(
    latitude: float,
    longitude: float,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    """Fetch and normalize hourly observations for one coordinate."""

    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_FIELDS),
        "forecast_days": 1,
        "timezone": "UTC",
    }
    owns_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(15.0))
    try:
        response = client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc
    finally:
        if owns_client:
            client.close()

    if not isinstance(payload, dict):
        raise OpenMeteoError("Open-Meteo response must be a JSON object")
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise OpenMeteoError("Open-Meteo response is missing hourly.time")

    times = hourly["time"]
    arrays: dict[str, list] = {}
    for field in HOURLY_FIELDS:
        values = hourly.get(field)
        if not isinstance(values, list) or len(values) != len(times):
            raise OpenMeteoError(f"Open-Meteo response has invalid hourly.{field}")
        arrays[field] = values

    actual_latitude = payload.get("latitude", latitude)
    actual_longitude = payload.get("longitude", longitude)
    observations = []
    for index, timestamp in enumerate(times):
        try:
            observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=timezone.utc)
            row_values = {field: arrays[field][index] for field in HOURLY_FIELDS}
            if any(value is not None and not isinstance(value, (int, float)) for value in row_values.values()):
                raise ValueError("hourly values must be numeric or null")
        except (AttributeError, TypeError, ValueError) as exc:
            raise OpenMeteoError(f"Invalid Open-Meteo hourly row at index {index}: {exc}") from exc

        observations.append(
            {
                "latitude": actual_latitude,
                "longitude": actual_longitude,
                "observed_at": observed_at,
                "temperature_c": row_values["temperature_2m"],
                "relative_humidity_pct": row_values["relative_humidity_2m"],
                "precipitation_mm": row_values["precipitation"],
                "wind_speed_kmh": row_values["wind_speed_10m"],
                "raw_payload": {
                    "time": timestamp,
                    **row_values,
                    "units": payload.get("hourly_units", {}),
                },
            }
        )
    return observations
