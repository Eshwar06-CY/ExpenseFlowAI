import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/live", tags=["Health"])
def live_check() -> Dict[str, str]:
    """
    Liveness probe.
    Confirms that the FastAPI service container process is running.
    """
    return {"status": "ok"}


@router.get("/ready", tags=["Health"])
def ready_check(response: Response, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness probe.
    Verifies that all backing services (MySQL database) are connected.
    Returns 503 if database connectivity is lost.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "detail": "Database connection offline"}


@router.get("/health", tags=["Health"])
def health_check(response: Response, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Production-ready health check endpoint.
    Validates service availability, database status, app version, and uptime.
    Returns 503 if any backing service is unhealthy.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    from app.main import get_uptime
    uptime = get_uptime()
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"

    overall = "healthy" if db_status == "healthy" else "unhealthy"

    return {
        "status": overall,
        "service": "expenseflow-backend",
        "version": "1.0.0",
        "database": db_status,
        "uptime": uptime_str,
    }
