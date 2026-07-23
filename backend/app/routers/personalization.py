"""
Personalization Router - ExpenseFlowAI Personalization & Privacy Center

API Endpoints:
- GET /api/personalization
- PUT /api/personalization/preferences
- POST /api/personalization/reset
- DELETE /api/personalization/behavior/{id}
- GET /api/personalization/export
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.personalization import (
    PersonalizationOverviewResponse,
    PersonalizationPreferencesUpdate,
    BehaviorDeleteResponse,
    AIDataExportResponse
)
from app.services.personalization_service import PersonalizationService
from app.services.privacy_service import PrivacyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalization", tags=["Personalization & Privacy Center"])


@router.get("", response_model=PersonalizationOverviewResponse, summary="Get AI Personalization Overview & Learned Behaviors")
def get_personalization_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonalizationOverviewResponse:
    """
    Returns AI personalization settings, overall confidence score, and active learned behaviors.
    """
    try:
        overview = PersonalizationService.get_personalization_overview(db, current_user.id)
        return PersonalizationOverviewResponse(**overview)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch personalization overview: {str(exc)}"
        ) from exc


@router.put("/preferences", response_model=PersonalizationOverviewResponse, summary="Update AI Personalization & Privacy Settings")
def update_personalization_preferences(
    payload: PersonalizationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonalizationOverviewResponse:
    """
    Updates user AI settings (coaching style, recommendation frequency, privacy controls).
    """
    try:
        PersonalizationService.update_preferences(db, current_user.id, payload)
        overview = PersonalizationService.get_personalization_overview(db, current_user.id)
        return PersonalizationOverviewResponse(**overview)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update personalization preferences: {str(exc)}"
        ) from exc


@router.post("/reset", response_model=PersonalizationOverviewResponse, summary="Delete All Learned AI Data ('Forget Everything')")
def reset_personalization_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonalizationOverviewResponse:
    """
    Executes complete AI data reset ("Forget Everything"):
    Deletes all learned behaviors, behavior tracking events, persistent memory entries,
    and resets preferences to default baseline.
    """
    try:
        overview = PrivacyService.reset_user_ai_data(db, current_user.id)
        return PersonalizationOverviewResponse(**overview)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset AI data: {str(exc)}"
        ) from exc


@router.delete("/behavior/{behavior_id}", response_model=BehaviorDeleteResponse, summary="Delete Single Learned Behavior ('Forget This Behavior')")
def delete_learned_behavior(
    behavior_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BehaviorDeleteResponse:
    """
    Deletes a specific learned behavior observation ("Forget This Behavior").
    Validates user ownership before deletion.
    """
    try:
        deleted = PersonalizationService.delete_behavior(db, current_user.id, behavior_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learned behavior with ID {behavior_id} not found or not owned by user."
            )
        return BehaviorDeleteResponse(
            success=True,
            message=f"Successfully deleted learned behavior {behavior_id}.",
            deleted_id=behavior_id
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete learned behavior: {str(exc)}"
        ) from exc


@router.get("/export", response_model=AIDataExportResponse, summary="Export Downloadable AI Data JSON")
def export_ai_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AIDataExportResponse:
    """
    Exports all preferences, learned behaviors, AI memory entries, and statistics
    as a downloadable JSON structure.
    """
    try:
        export_data = PrivacyService.export_user_ai_data(db, current_user.id)
        return AIDataExportResponse(**export_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export AI data: {str(exc)}"
        ) from exc
