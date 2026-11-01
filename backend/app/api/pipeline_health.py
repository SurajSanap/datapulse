"""Pipeline health summary endpoint for dashboard consumers."""

from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import PipelineRun
from app.schemas.pipeline_run import PipelineHealthSummary

router = APIRouter(tags=["pipeline-health"])


@router.get("/pipeline-health", response_model=list[PipelineHealthSummary])
def get_pipeline_health(db: Session = Depends(get_db)) -> list[dict]:
    """Return execution counts and the latest run for each pipeline."""
    aggregates = (
        select(
            PipelineRun.pipeline_name.label("pipeline_name"),
            func.count(PipelineRun.id).label("total_runs"),
            func.sum(case((PipelineRun.status == "success", 1), else_=0)).label(
                "successful_runs"
            ),
            func.sum(case((PipelineRun.status == "failed", 1), else_=0)).label(
                "failed_runs"
            ),
            func.sum(case((PipelineRun.status == "running", 1), else_=0)).label(
                "running_runs"
            ),
        )
        .group_by(PipelineRun.pipeline_name)
        .subquery()
    )

    ranked_runs = (
        select(
            PipelineRun.pipeline_name.label("pipeline_name"),
            PipelineRun.started_at.label("latest_run_at"),
            PipelineRun.status.label("latest_status"),
            func.row_number()
            .over(
                partition_by=PipelineRun.pipeline_name,
                order_by=(PipelineRun.started_at.desc(), PipelineRun.id.desc()),
            )
            .label("run_rank"),
        )
        .subquery()
    )

    statement = (
        select(
            aggregates.c.pipeline_name,
            aggregates.c.total_runs,
            aggregates.c.successful_runs,
            aggregates.c.failed_runs,
            aggregates.c.running_runs,
            ranked_runs.c.latest_run_at,
            ranked_runs.c.latest_status,
        )
        .select_from(aggregates)
        .join(
            ranked_runs,
            and_(
                aggregates.c.pipeline_name == ranked_runs.c.pipeline_name,
                ranked_runs.c.run_rank == 1,
            ),
        )
        .order_by(aggregates.c.pipeline_name.asc())
    )
    return [dict(row) for row in db.execute(statement).mappings().all()]
