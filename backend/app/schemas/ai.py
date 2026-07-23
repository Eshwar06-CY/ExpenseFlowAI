"""
Pydantic Schemas for AI Financial Advisor Endpoint - ExpenseFlowAI
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: Optional[str] = Field(
        None,
        max_length=4000,
        description="The user's question or financial prompt",
        examples=["How can I save more money this month?"]
    )
    prompt: Optional[str] = Field(
        None,
        max_length=4000,
        description="User prompt alias"
    )
    period: Optional[str] = Field(
        "30d",
        description="Financial window to evaluate: 7d, 30d, 90d, 1y",
        examples=["30d"]
    )

    def get_text(self) -> str:
        text = (self.message or self.prompt or "").strip()
        if not text:
            raise ValueError("Message or prompt text is required.")
        return text


class AIChatResponse(BaseModel):
    response: str = Field(..., description="The AI Advisor's financial advice response")
    provider: str = Field("gemini", description="Configured LLM provider name")
    model: str = Field("gemini-3.6-flash", description="Model identifier used for inference")


class AIHealthResponse(BaseModel):
    provider: str = Field(..., description="LLM Provider identifier")
    model: str = Field(..., description="Configured LLM model name")
    status: str = Field(..., description="Provider status: healthy, degraded, or unhealthy")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed diagnostic health metadata")


class FinancialSnapshotSchema(BaseModel):
    income: float = Field(0.0, description="Total income for the period")
    expenses: float = Field(0.0, description="Total expenses for the period")
    savings: float = Field(0.0, description="Net savings for the period")
    savings_rate: float = Field(0.0, description="Savings rate percentage")
    health_score: int = Field(0, description="Financial health score on 0-100 scale")
    health_status: str = Field("N/A", description="Health score status rating")
    reserve_months: float = Field(0.0, description="Emergency fund reserve in months")
    budget_adherence_pct: float = Field(100.0, description="Budget adherence percentage")
    bill_reliability_pct: float = Field(100.0, description="Bill payment reliability percentage")


class AICoachRequest(BaseModel):
    period: Optional[str] = Field("30d", description="Financial window to evaluate: 7d, 30d, 90d, 1y")
    focus_area: Optional[str] = Field(None, description="Optional focus area e.g. savings, debt, budget, investments")


from typing import List

class AIFinancialCoachResponse(BaseModel):
    summary: str = Field(..., description="Executive summary observation of financial standing")
    financial_snapshot: FinancialSnapshotSchema = Field(..., description="Verified snapshot of metrics")
    strengths: List[str] = Field(default_factory=list, description="Key positive financial observations")
    risks: List[str] = Field(default_factory=list, description="Identified financial risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Actionable, prioritized recommendations")
    next_month_focus: List[str] = Field(default_factory=list, description="Focus areas for the upcoming month")
    encouragement: str = Field(..., description="Positive reinforcement statement")
    confidence: float = Field(0.95, description="Confidence score of the coaching assessment")

