"""Air quality data source module."""


def fetch_air_quality(city: str) -> dict:
    return {
        "city": city,
        "source": "air_quality",
        "status": "not_implemented",
    }
