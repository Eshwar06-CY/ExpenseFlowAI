"""
Pydantic Schemas for AI Financial Copilot Daily Briefing - ExpenseFlowAI
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GoalSummaryItem(BaseModel):
    goal_name: str = Field(..., description="Name of the financial goal")
    target_amount: float = Field(..., description="Target cost of the goal")
    current_saved: float = Field(..., description="Currently accumulated savings")
    progress_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of goal completed")
    status: str = Field(..., description="Goal status e.g. ON_TRACK, FEASIBLE_WITH_ADJUSTMENTS, HIGH_RISK")


class UpcomingEventItem(BaseModel):
    title: str = Field(..., description="Event or bill description")
    type: str = Field(..., description="Event type: BILL, SUBSCRIPTION, MILESTONE")
    amount: float = Field(..., description="Associated monetary amount")
    due_date: str = Field(..., description="Due date in YYYY-MM-DD format")
    days_remaining: int = Field(..., description="Days remaining until due date")


class AIFinancialCopilotResponse(BaseModel):
    greeting: str = Field(..., description="Personalized greeting (e.g. Good Morning 👋)")
    health_score: int = Field(..., ge=0, le=100, description="Composite financial health score (0-100)")
    health_status: str = Field(..., description="Financial health rating status (e.g. Excellent, Healthy, Vulnerable)")
    highlights: List[str] = Field(default_factory=list, description="Key positive financial highlights of the day")
    alerts: List[str] = Field(default_factory=list, description="Urgent warnings or spending alerts requiring attention")
    recommendations: List[str] = Field(default_factory=list, description="Prioritized, actionable daily recommendations")
    goal_updates: List[GoalSummaryItem] = Field(default_factory=list, description="Status snapshot of user financial goals")
    upcoming_events: List[UpcomingEventItem] = Field(default_factory=list, description="Upcoming bills, subscriptions, or financial deadlines")
    encouragement: str = Field(..., description="Positive motivational closing statement")
