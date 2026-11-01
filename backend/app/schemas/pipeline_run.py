"""API response schemas for pipeline runs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PipelineRunRead(BaseModel):
    """Public representation of one pipeline execution."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pipeline_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    records_processed: int
    error_message: str | None
