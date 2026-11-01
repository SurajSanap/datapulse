"""Open-Meteo pipeline lifecycle and database persistence."""

from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.ingestion.open_meteo import fetch_hourly_weather
from app.models.pipeline_run import PipelineRun
from app.models.weather_observation import WeatherObservation

PIPELINE_NAME = "open_meteo_weather"


def run_weather_pipeline(
    db: Session,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    client: httpx.Client | None = None,
    fetcher=fetch_hourly_weather,
) -> PipelineRun:
    """Fetch weather, persist hourly observations, and store the run outcome."""

    run = PipelineRun(pipeline_name=PIPELINE_NAME, status="running", records_processed=0)
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        rows: list[dict[str, Any]] = fetcher(latitude, longitude, client)
        for row in rows:
            db.add(WeatherObservation(**row))
        run.records_processed = len(rows)
        run.status = "success"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        db.rollback()
        failed_run = db.get(PipelineRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.completed_at = datetime.now(timezone.utc)
            failed_run.error_message = str(exc)[:4000]
            db.commit()
        raise
