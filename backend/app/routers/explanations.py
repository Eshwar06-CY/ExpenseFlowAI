"""
Explainable AI (XAI) API Router - ExpenseFlowAI

Endpoints:
- GET /api/v1/explanations/{feature}/{target_id} (Retrieve structured explanation)
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.explanation import ExplanationDTO, ExplanationResponse
from app.services.explainability_service import ExplainabilityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/explanations", tags=["Explainable AI"])


@router.get("/{feature}/{target_id}", response_model=ExplanationResponse, summary="Get Structured Explanation for AI Output")
def get_ai_explanation(
    feature: str,
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExplanationResponse:
    """
    Returns a transparent, structured explanation detailing:
    - Why the recommendation or output was generated
    - Data sources used
    - Exact FinanceEngine mathematical metrics
    - Confidence score (0.0 to 1.0)
    - System assumptions & limitations
    - Suggested actions
    """
    try:
        dto = ExplainabilityService.get_explanation(
            db=db,
            user_id=current_user.id,
            feature=feature,
            target_id=target_id
        )
        return ExplanationResponse(
            answer=f"Explanation generated for feature '{feature}' ({target_id}).",
            explanation=dto
        )
    except Exception as exc:
        logger.error("Failed to generate explanation: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(exc)}"
        ) from exc
