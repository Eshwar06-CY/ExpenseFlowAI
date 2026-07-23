"""
FastAPI Router for AI Financial Advisor & Coaching Endpoints - ExpenseFlowAI
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.routers.deps import get_current_user
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse, AIHealthResponse, AICoachRequest, AIFinancialCoachResponse
from app.ai.advisor import AIAdvisorService
from app.services.chat_stream import ChatStreamService
from app.services.ai_financial_coach import AIFinancialCoachService, get_ai_coach_service

router = APIRouter()


def get_advisor_service() -> AIAdvisorService:
    """
    Dependency provider for AIAdvisorService instance.
    Enables easy mocking in unit tests.
    """
    return AIAdvisorService()


def get_chat_stream_service() -> ChatStreamService:
    """
    Dependency provider for ChatStreamService instance.
    Enables easy mocking in unit tests.
    """
    return ChatStreamService()


@router.get("/health", response_model=AIHealthResponse, summary="Get AI Provider Health Status")
def get_ai_health(
    advisor_service: AIAdvisorService = Depends(get_advisor_service)
) -> AIHealthResponse:
    """
    Returns the health status and connectivity of the configured LLM provider (Google Gemini 3.6 Flash / Hybrid).
    """
    health = advisor_service.health_check()
    return AIHealthResponse(
        provider=health.get("provider", "gemini"),
        model=health.get("model", settings.GEMINI_MODEL),
        status=health.get("status", "unhealthy"),
        details=health.get("details")
    )


@router.post("/chat", response_model=AIChatResponse, summary="Chat with AI Financial Advisor")
def chat_with_advisor(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    advisor_service: AIAdvisorService = Depends(get_advisor_service)
) -> AIChatResponse:
    """
    Authenticated endpoint to receive personalized financial advice based on
    verified FinanceEngine metrics.
    """
    try:
        user_msg = payload.get_text()
        result = advisor_service.ask(
            db=db,
            user_id=current_user.id,
            message=user_msg,
            period=payload.period or "30d"
        )
        return AIChatResponse(
            response=result.get("response", ""),
            provider=result.get("provider", "gemini"),
            model=result.get("model", settings.GEMINI_MODEL)
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating financial advice: {str(exc)}"
        ) from exc


@router.post("/chat/stream", summary="Stream response from AI Financial Advisor")
async def chat_with_advisor_stream(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stream_service: ChatStreamService = Depends(get_chat_stream_service)
):
    """
    Authenticated streaming endpoint yielding token chunks as Server-Sent Events (SSE).
    """
    try:
        user_msg = payload.get_text()
        generator = stream_service.stream_chat_response(
            db=db,
            user_id=current_user.id,
            user_message=user_msg,
            period=payload.period or "30d"
        )
        headers = {
            "content-type": "text/event-stream",
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "x-accel-buffering": "no"
        }
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers=headers
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Streaming service error: {str(exc)}"
        ) from exc


@router.get("/coach", response_model=AIFinancialCoachResponse, summary="Get AI Financial Coaching Assessment")
def get_financial_coaching(
    period: str = Query("30d", description="Analysis timeframe (e.g. 7d, 30d, 90d)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    coach_service: AIFinancialCoachService = Depends(get_ai_coach_service)
) -> AIFinancialCoachResponse:
    """
    Returns structured financial coaching assessment based on verified FinanceEngine metrics.
    """
    try:
        report = coach_service.generate_coaching_report(db=db, user_id=current_user.id, period=period)
        return AIFinancialCoachResponse(**report)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coaching assessment failed: {str(exc)}"
        ) from exc


@router.post("/coach/analyze", response_model=AIFinancialCoachResponse, summary="Analyze Specific Coaching Focus Area")
def analyze_financial_coaching_focus(
    payload: AICoachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    coach_service: AIFinancialCoachService = Depends(get_ai_coach_service)
) -> AIFinancialCoachResponse:
    """
    Generates a targeted financial coaching report focusing on a specific financial area.
    """
    try:
        report = coach_service.generate_coaching_report(
            db=db,
            user_id=current_user.id,
            period=payload.period or "30d",
            focus_area=payload.focus_area
        )
        return AIFinancialCoachResponse(**report)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Targeted coaching analysis failed: {str(exc)}"
        ) from exc
