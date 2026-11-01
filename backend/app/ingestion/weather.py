"""Command-line entry point for the Open-Meteo weather pipeline."""

import os

from app.db.session import SessionLocal
from app.ingestion.weather_pipeline import run_weather_pipeline


def main() -> None:
    latitude = float(os.getenv("OPEN_METEO_LATITUDE", "28.6139"))
    longitude = float(os.getenv("OPEN_METEO_LONGITUDE", "77.2090"))
    with SessionLocal() as db:
        run = run_weather_pipeline(db, latitude=latitude, longitude=longitude)
    print(
        f"Pipeline {run.pipeline_name} {run.status}: "
        f"{run.records_processed} observations (run id {run.id})"
    )


if __name__ == "__main__":
    main()
