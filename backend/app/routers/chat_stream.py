"""
Chat Stream Router - ExpenseFlowAI Real-Time Streaming AI Chat

API Endpoints:
- POST /api/v1/ai/chat/stream (SSE StreamingResponse)
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.services.chat_stream import ChatStreamService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/chat", tags=["AI Real-Time Streaming Chat"])


class ChatStreamRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=4000, description="User question or prompt for AI assistant")
    prompt: Optional[str] = Field(None, max_length=4000, description="User prompt alias")
    period: Optional[str] = Field("30d", description="Analysis period e.g. 7d, 30d, 90d", examples=["30d"])
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Recent conversation turns context")

    @model_validator(mode='after')
    def validate_non_empty_prompt(self):
        text = (self.message or self.prompt or "").strip()
        if not text:
            raise ValueError("Prompt or message text is required and cannot be empty.")
        return self

    def get_prompt_text(self) -> str:
        return (self.message or self.prompt or "").strip()


def get_chat_stream_service() -> ChatStreamService:
    """
    Dependency provider for ChatStreamService.
    Allows easy mocking in unit tests.
    """
    return ChatStreamService()


@router.post("/stream", summary="Stream Real-Time AI Chat Response (Server-Sent Events)")
async def stream_ai_chat(
    payload: ChatStreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stream_service: ChatStreamService = Depends(get_chat_stream_service)
) -> StreamingResponse:
    """
    Real-time token-by-token streaming endpoint using Server-Sent Events (SSE).
    Media-Type: text/event-stream
    Returns stream data chunks formatted as:
      data: {"type": "token", "content": "..."}
      data: {"type": "done"}
    """
    try:
        user_msg = payload.get_prompt_text()
        generator = stream_service.stream_chat_response(
            db=db,
            user_id=current_user.id,
            user_message=user_msg,
            period=payload.period or "30d",
            chat_history=payload.chat_history or []
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

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to initialize chat stream: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize streaming response: {str(exc)}"
        ) from exc
