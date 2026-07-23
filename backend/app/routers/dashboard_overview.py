"""
Dashboard Overview Router - ExpenseFlowAI Command Center

API Endpoints:
- GET /api/v1/dashboard/overview (Unified Command Center Payload)
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Financial Command Center"])


def get_dashboard_service() -> DashboardService:
    """
    Dependency provider for DashboardService.
    Allows easy mocking in unit tests.
    """
    return DashboardService()


@router.get("/overview", summary="Get Unified AI Command Center Dashboard Overview")
def get_command_center_overview(
    period: str = Query("30d", description="Analysis window e.g. 7d, 30d, 90d, 1y"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
    """
    Returns the unified AI Command Center dashboard payload containing:
    Health score, net worth, metrics, 30-day forecast, AI insights, budget burn rates,
    goal progress, bills timeline, digital twin presets, and executive summary.
    """
    try:
        overview = dashboard_service.get_command_center_overview(
            db=db,
            user_id=current_user.id,
            period=period
        )
        return overview
    except Exception as exc:
        logger.error("Failed to generate command center overview: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard overview: {str(exc)}"
        ) from exc
