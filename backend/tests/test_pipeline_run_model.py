import unittest

from app.db.base import Base
from app.models import PipelineRun


class PipelineRunModelTests(unittest.TestCase):
    def test_pipeline_run_table_has_expected_columns(self) -> None:
        self.assertEqual(
            set(PipelineRun.__table__.columns.keys()),
            {
                "id",
                "pipeline_name",
                "status",
                "started_at",
                "completed_at",
                "records_processed",
                "error_message",
                "created_at",
            },
        )

    def test_pipeline_run_defaults_and_constraints(self) -> None:
        table = PipelineRun.__table__
        self.assertIs(Base.metadata.tables["pipeline_runs"], table)
        self.assertEqual(table.c.pipeline_name.type.length, 255)
        self.assertEqual(table.c.status.type.length, 20)
        self.assertEqual(table.c.records_processed.server_default.arg, "0")
        self.assertIn(
            "ck_pipeline_runs_records_processed_nonnegative",
            {constraint.name for constraint in table.constraints},
        )
        self.assertIn("ix_pipeline_runs_pipeline_name", {index.name for index in table.indexes})


if __name__ == "__main__":
    unittest.main()
