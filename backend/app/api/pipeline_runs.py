"""Read-only API for pipeline execution history."""

from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import PipelineRun
from app.schemas.pipeline_run import PipelineRunRead

router = APIRouter(tags=["pipeline-runs"])


class PipelineRunStatus(StrEnum):
    """Supported lifecycle values written by pipeline runners."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@router.get("/pipeline-runs", response_model=list[PipelineRunRead])
def list_pipeline_runs(
    pipeline_name: str | None = Query(default=None, min_length=1, max_length=255),
    status: PipelineRunStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PipelineRun]:
    """Return a page of runs, newest first with a stable ID tie-breaker."""
    statement = select(PipelineRun)
    if pipeline_name is not None:
        statement = statement.where(PipelineRun.pipeline_name == pipeline_name)
    if status is not None:
        statement = statement.where(PipelineRun.status == status.value)

    statement = (
        statement.order_by(PipelineRun.started_at.desc(), PipelineRun.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


@router.get("/pipeline-runs/{run_id}", response_model=PipelineRunRead)
def get_pipeline_run(run_id: int, db: Session = Depends(get_db)) -> PipelineRun:
    """Return one pipeline run or 404 when the ID is unknown."""
    run = db.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run {run_id} not found",
        )
    return run
