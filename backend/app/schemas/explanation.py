"""
Pydantic Schemas for Explainable AI (XAI) Framework - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExplanationDTO(BaseModel):
    """
    Structured Explainable AI Data Transfer Object for recommendations,
    forecasts, insights, notifications, strategy, and digital twin scenarios.
    """
    feature: str = Field(..., description="Feature identifier e.g. dashboard, forecast, budget, goal, digital_twin, notification")
    target_id: str = Field(..., description="Target object identifier e.g. highest_expense, 1, 30d, salary_increase")
    reason: str = Field(..., description="Transparent explanation of why this AI output was generated")
    data_used: List[str] = Field(default_factory=list, description="Verified data sources that influenced the output")
    finance_engine_metrics: Dict[str, Any] = Field(default_factory=dict, description="Verified mathematical outputs from FinanceEngine")
    confidence: float = Field(0.90, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    assumptions: List[str] = Field(default_factory=list, description="Key system assumptions made")
    limitations: List[str] = Field(default_factory=list, description="Known system limitations or external variables")
    related_features: List[str] = Field(default_factory=list, description="Related ExpenseFlowAI features")
    suggested_actions: List[str] = Field(default_factory=list, description="Recommended next actions")


class ExplanationResponse(BaseModel):
    """
    Envelope response for AI features with explanation metadata.
    """
    answer: Optional[str] = None
    explanation: ExplanationDTO
