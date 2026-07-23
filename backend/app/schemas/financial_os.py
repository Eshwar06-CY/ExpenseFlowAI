"""
Pydantic Schemas for AI Personal Finance Operating System (Financial OS) - ExpenseFlowAI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SuggestedActionItem(BaseModel):
    title: str = Field(..., description="Short action title e.g. Increase grocery budget")
    tool_name: str = Field(..., description="Target tool name e.g. BudgetTool, GoalTool, ReminderTool")
    action: str = Field(..., description="Target tool action e.g. create_budget, set_reminder")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Recommended action parameters")
    impact_description: str = Field(..., description="Expected positive financial outcome")


class TodaySnapshot(BaseModel):
    health_score: int = Field(..., ge=0, le=100, description="Financial health score (0-100)")
    health_status: str = Field(..., description="Health rating status e.g. Excellent, Healthy")
    total_balance: float = Field(..., description="Total available balance across active accounts")
    period_income: float = Field(..., description="Income earned in selected period")
    period_expense: float = Field(..., description="Expenses spent in selected period")
    monthly_surplus: float = Field(..., description="Net cashflow surplus")


class AIFinancialOSResponse(BaseModel):
    today: TodaySnapshot = Field(..., description="Financial OS today's high level metrics")
    priorities: List[str] = Field(default_factory=list, description="Top prioritized financial focus items (Max 3)")
    opportunities: List[str] = Field(default_factory=list, description="Identified financial growth/savings opportunities (Max 3)")
    alerts: List[str] = Field(default_factory=list, description="Urgent risk alerts or spending warnings (Max 3)")
    predictions: List[str] = Field(default_factory=list, description="Forecasted cashflow & reserve trend predictions")
    actions: List[SuggestedActionItem] = Field(default_factory=list, description="Directly executable tool actions (Max 3)")
    motivation: str = Field(..., description="Motivational closing guidance")
