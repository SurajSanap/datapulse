"""Weather data source module."""


def fetch_weather(city: str) -> dict:
    return {
        "city": city,
        "source": "weather",
        "status": "not_implemented",
    }
