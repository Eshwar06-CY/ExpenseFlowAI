"""
Pydantic Schemas for AI Financial Strategy Planner - ExpenseFlowAI
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MonthlyActionItem(BaseModel):
    month_number: int = Field(..., ge=1, le=12, description="Month sequence number (1-12)", examples=[1])
    title: str = Field(..., description="Action title e.g. 'Increase emergency fund to 6 months'", examples=["Increase emergency fund"])
    description: str = Field(..., description="Action details and specific quantitative target", examples=["Allocate 40% of net surplus to emergency reserve."])
    target_category: Optional[str] = Field("General", description="Category context e.g. Savings, Debt, Budget, Investment", examples=["Savings"])


class AIStrategyPlanResponse(BaseModel):
    current_health: int = Field(..., ge=0, le=100, description="Baseline financial health score (0-100)", examples=[74])
    priorities: List[str] = Field(..., description="Prioritized list of financial directives (Top 5 priorities)", examples=["Increase emergency fund to 6 months."])
    one_year_plan: List[str] = Field(..., description="1-Year tactical execution milestones", examples=["Eliminate high-interest credit card debt."])
    three_year_plan: List[str] = Field(..., description="3-Year strategic growth milestones", examples=["Accumulate $50,000 liquid investment portfolio."])
    five_year_plan: List[str] = Field(..., description="5-Year wealth & independence milestones", examples=["Achieve complete debt-free financial independence."])
    monthly_actions: List[MonthlyActionItem] = Field(default_factory=list, description="Month-by-month 12-month execution checklist")
    risks: List[str] = Field(default_factory=list, description="Identified strategic risk factors", examples=["High food delivery expenditure ratio."])
    confidence: float = Field(..., ge=0.0, le=1.0, description="Plan confidence rating between 0.0 and 1.0", examples=[0.93])
