"""Focused API tests for listing pipeline runs."""

import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models import PipelineRun


class PipelineRunsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        PipelineRun.__table__.create(self.engine)
        self.SessionTest = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

        def override_get_db():
            with self.SessionTest() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        self._seed_runs()

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def _seed_runs(self) -> None:
        now = datetime.now(timezone.utc)
        with self.SessionTest() as db:
            db.add_all(
                [
                    PipelineRun(
                        pipeline_name="open_meteo_weather",
                        status="success",
                        started_at=now - timedelta(minutes=3),
                        records_processed=24,
                    ),
                    PipelineRun(
                        pipeline_name="open_meteo_weather",
                        status="failed",
                        started_at=now - timedelta(minutes=2),
                        records_processed=0,
                        error_message="upstream unavailable",
                    ),
                    PipelineRun(
                        pipeline_name="other_pipeline",
                        status="running",
                        started_at=now - timedelta(minutes=1),
                        records_processed=0,
                    ),
                ]
            )
            db.commit()

    def test_filters_by_pipeline_name_and_status(self) -> None:
        response = self.client.get(
            "/pipeline-runs",
            params={"pipeline_name": "open_meteo_weather", "status": "failed"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["error_message"], "upstream unavailable")

    def test_paginates_with_newest_runs_first(self) -> None:
        response = self.client.get("/pipeline-runs", params={"limit": 1, "offset": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["pipeline_name"], "open_meteo_weather")
        self.assertEqual(response.json()[0]["status"], "failed")

    def test_returns_empty_list_for_no_matches(self) -> None:
        response = self.client.get("/pipeline-runs", params={"pipeline_name": "missing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_rejects_invalid_status(self) -> None:
        response = self.client.get("/pipeline-runs", params={"status": "unknown"})
        self.assertEqual(response.status_code, 422)

    def test_rejects_out_of_range_pagination(self) -> None:
        self.assertEqual(self.client.get("/pipeline-runs", params={"limit": 101}).status_code, 422)
        self.assertEqual(self.client.get("/pipeline-runs", params={"offset": -1}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
