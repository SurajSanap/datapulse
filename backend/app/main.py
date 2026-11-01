from fastapi import FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.pipeline_health import router as pipeline_health_router
from app.api.pipeline_runs import router as pipeline_runs_router
from app.db.session import check_database_connection

app = FastAPI(title="DataPulse API", version="0.2.0")
app.include_router(pipeline_runs_router)
app.include_router(pipeline_health_router)


@app.get("/")
def read_root() -> dict:
    return {"message": "Welcome to DataPulse API"}


@app.get("/health")
def healthcheck() -> dict:
    """Liveness check: confirms that the API process is responding."""
    return {"status": "ok"}


@app.get("/health/ready")
def readiness_check() -> dict:
    """Readiness check: confirms that the API can reach PostgreSQL."""
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return {"status": "ready", "database": "connected"}
