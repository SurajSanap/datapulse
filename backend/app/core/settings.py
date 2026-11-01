from dataclasses import dataclass


@dataclass
class WeatherSourceConfig:
    api_key: str = ""
    base_url: str = "https://api.weatherapi.com/v1"


@dataclass
class AirQualitySourceConfig:
    api_key: str = ""
    base_url: str = "https://api.openaq.org/v3"
