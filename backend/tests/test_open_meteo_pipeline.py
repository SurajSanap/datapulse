import unittest
from datetime import timezone

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.ingestion.open_meteo import HOURLY_FIELDS, OpenMeteoError, fetch_hourly_weather
from app.ingestion.weather_pipeline import run_weather_pipeline
from app.models import PipelineRun, WeatherObservation


class OpenMeteoPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def _payload(self) -> dict:
        return {
            "latitude": 28.6,
            "longitude": 77.2,
            "hourly_units": {name: "test" for name in HOURLY_FIELDS},
            "hourly": {
                "time": ["2026-11-02T00:00", "2026-11-02T01:00"],
                "temperature_2m": [20.5, 21.0],
                "relative_humidity_2m": [55, 53],
                "precipitation": [0.0, 0.2],
                "wind_speed_10m": [8.0, 9.5],
            },
        }

    def test_fetch_parses_hourly_rows_and_preserves_source_values(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=self._payload())
        )
        with httpx.Client(transport=transport) as client:
            rows = fetch_hourly_weather(28.6139, 77.2090, client)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["temperature_c"], 20.5)
        self.assertEqual(rows[0]["raw_payload"]["relative_humidity_2m"], 55)
        self.assertEqual(rows[0]["observed_at"].tzinfo, timezone.utc)

    def test_fetch_rejects_mismatched_hourly_arrays(self) -> None:
        payload = self._payload()
        payload["hourly"]["precipitation"] = [0.0]
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        with httpx.Client(transport=transport) as client:
            with self.assertRaises(OpenMeteoError):
                fetch_hourly_weather(28.6139, 77.2090, client)

    def test_pipeline_persists_observations_and_successful_run(self) -> None:
        payload = self._payload()
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        with httpx.Client(transport=transport) as client:
            run = run_weather_pipeline(self.db, client=client)

        self.assertEqual(run.status, "success")
        self.assertEqual(run.records_processed, 2)
        self.assertIsNotNone(run.completed_at)
        observations = list(self.db.scalars(select(WeatherObservation)).all())
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].raw_payload["time"], "2026-11-02T00:00")

    def test_pipeline_records_failed_run_when_fetch_fails(self) -> None:
        def fail_fetcher(*args, **kwargs):
            raise OpenMeteoError("upstream unavailable")

        with self.assertRaises(OpenMeteoError):
            run_weather_pipeline(self.db, fetcher=fail_fetcher)

        run = self.db.scalar(select(PipelineRun))
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.error_message, "upstream unavailable")
        self.assertIsNotNone(run.completed_at)


if __name__ == "__main__":
    unittest.main()
