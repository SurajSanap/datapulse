"""Focused API tests for pipeline history and health summaries."""

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

    def test_retrieves_pipeline_run_details(self) -> None:
        listed = self.client.get("/pipeline-runs", params={"status": "failed"}).json()
        run_id = listed[0]["id"]

        response = self.client.get(f"/pipeline-runs/{run_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pipeline_name"], "open_meteo_weather")
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual(response.json()["records_processed"], 0)
        self.assertEqual(response.json()["error_message"], "upstream unavailable")
        self.assertIn("started_at", response.json())
        self.assertIn("completed_at", response.json())

    def test_returns_404_for_unknown_pipeline_run(self) -> None:
        response = self.client.get("/pipeline-runs/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Pipeline run 999 not found")

    def test_pipeline_health_summarizes_mixed_statuses_in_stable_order(self) -> None:
        response = self.client.get("/pipeline-health")

        self.assertEqual(response.status_code, 200)
        summaries = response.json()
        self.assertEqual(
            [summary["pipeline_name"] for summary in summaries],
            ["open_meteo_weather", "other_pipeline"],
        )

        weather = summaries[0]
        self.assertEqual(weather["total_runs"], 2)
        self.assertEqual(weather["successful_runs"], 1)
        self.assertEqual(weather["failed_runs"], 1)
        self.assertEqual(weather["running_runs"], 0)
        self.assertEqual(weather["latest_status"], "failed")
        self.assertIsNotNone(weather["latest_run_at"])

        other = summaries[1]
        self.assertEqual(other["total_runs"], 1)
        self.assertEqual(other["successful_runs"], 0)
        self.assertEqual(other["failed_runs"], 0)
        self.assertEqual(other["running_runs"], 1)
        self.assertEqual(other["latest_status"], "running")

    def test_pipeline_health_returns_empty_list_without_run_history(self) -> None:
        with self.SessionTest() as db:
            db.query(PipelineRun).delete()
            db.commit()

        response = self.client.get("/pipeline-health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


if __name__ == "__main__":
    unittest.main()
