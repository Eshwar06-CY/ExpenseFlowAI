"""
FastAPI Router for AI Financial Advisor Endpoints - ExpenseFlowAI
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.deps import get_current_user
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse, AIHealthResponse
from app.ai.advisor import AIAdvisorService

router = APIRouter()


def get_advisor_service() -> AIAdvisorService:
    """
    Dependency provider for AIAdvisorService instance.
    Enables easy mocking in unit tests.
    """
    return AIAdvisorService()


@router.get("/health", response_model=AIHealthResponse, summary="Get AI Provider Health Status")
def get_ai_health(
    advisor_service: AIAdvisorService = Depends(get_advisor_service)
) -> AIHealthResponse:
    """
    Returns the health status and connectivity of the configured LLM provider (Ollama).
    """
    health = advisor_service.health_check()
    return AIHealthResponse(
        provider=health.get("provider", "ollama"),
        model=health.get("model", "qwen3:8b"),
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
        result = advisor_service.ask(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            period=payload.period or "30d"
        )
        return AIChatResponse(
            response=result.get("response", ""),
            provider=result.get("provider", "ollama"),
            model=result.get("model", "qwen3:8b")
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
    advisor_service: AIAdvisorService = Depends(get_advisor_service)
):
    """
    Authenticated streaming endpoint yielding token chunks as Server-Sent Events / plain stream.
    """
    try:
        generator = advisor_service.ask_stream(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            period=payload.period or "30d"
        )
        return StreamingResponse(generator, media_type="text/plain")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Streaming service error: {str(exc)}"
        ) from exc
