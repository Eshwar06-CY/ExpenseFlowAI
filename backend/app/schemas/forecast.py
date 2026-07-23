"""
Pydantic Schemas for Predictive Cash Flow Engine - ExpenseFlowAI
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ForecastItem(BaseModel):
    days: int = Field(..., description="Forecast horizon in days e.g. 7, 30, 90")
    period_label: str = Field(..., description="Horizon label e.g. '7-Day', '30-Day', '90-Day'")
    expected_balance: float = Field(..., description="Projected liquid balance at end of horizon")
    projected_income: float = Field(..., description="Projected income for the horizon")
    projected_expenses: float = Field(..., description="Projected expenses for the horizon")
    net_change: float = Field(..., description="Projected net balance change")
    savings_projection: float = Field(..., description="Projected savings accumulated")
    risk_events: List[str] = Field(default_factory=list, description="Upcoming bills or cashflow risk events")


class AICashFlowForecastResponse(BaseModel):
    forecast: List[ForecastItem] = Field(..., description="7, 30, and 90 day cashflow forecast projections")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Forecast confidence score between 0.0 and 1.0")
    warnings: List[str] = Field(default_factory=list, description="Risk warnings e.g. balance depletion or bill burden")
    opportunities: List[str] = Field(default_factory=list, description="Cashflow optimization opportunities")
    explanation: str = Field(..., description="AI narrative explaining why balances change, upcoming risks, and improvements")
