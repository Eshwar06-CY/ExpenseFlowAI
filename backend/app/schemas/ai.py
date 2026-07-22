"""
Pydantic Schemas for AI Financial Advisor Endpoint - ExpenseFlowAI
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question or financial prompt",
        examples=["How can I save more money this month?"]
    )
    period: Optional[str] = Field(
        "30d",
        description="Financial window to evaluate: 7d, 30d, 90d, 1y",
        examples=["30d"]
    )


class AIChatResponse(BaseModel):
    response: str = Field(..., description="The AI Advisor's financial advice response")
    provider: str = Field("ollama", description="Configured LLM provider name")
    model: str = Field("qwen3:8b", description="Model identifier used for inference")


class AIHealthResponse(BaseModel):
    provider: str = Field(..., description="LLM Provider identifier")
    model: str = Field(..., description="Configured LLM model name")
    status: str = Field(..., description="Provider status: healthy, degraded, or unhealthy")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed diagnostic health metadata")
