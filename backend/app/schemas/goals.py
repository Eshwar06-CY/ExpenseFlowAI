"""
Pydantic Schemas for AI Goal Planner - ExpenseFlowAI
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class GoalFeasibilityStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    FEASIBLE_WITH_ADJUSTMENTS = "FEASIBLE_WITH_ADJUSTMENTS"
    HIGH_RISK = "HIGH_RISK"
    UNFEASIBLE = "UNFEASIBLE"
    ALREADY_ACHIEVED = "ALREADY_ACHIEVED"


class AIGoalPlanRequest(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=100, description="Title of the goal e.g. MacBook Pro, Europe Trip", examples=["MacBook Pro"])
    target_amount: float = Field(..., gt=0, description="Total target amount in user currency", examples=[180000.0])
    target_date: Optional[str] = Field(None, description="Optional target target date string (YYYY-MM-DD)", examples=["2027-03-01"])
    current_saved: Optional[float] = Field(0.0, ge=0.0, description="Amount already accumulated towards this goal", examples=[20000.0])


class AIGoalPlanResponse(BaseModel):
    goal_name: str = Field(..., description="Name of the evaluated financial goal")
    target_amount: float = Field(..., description="Target cost of the goal")
    current_saved: float = Field(0.0, description="Current accumulated savings towards goal")
    monthly_required: float = Field(..., description="Monthly contribution required to hit deadline")
    monthly_surplus: float = Field(..., description="Verified net monthly surplus from FinanceEngine")
    status: GoalFeasibilityStatus = Field(..., description="Feasibility status rating")
    completion_probability: float = Field(..., ge=0.0, le=1.0, description="Probability score of achieving target (0.0 to 1.0)")
    estimated_completion_date: str = Field(..., description="Estimated completion date (YYYY-MM-DD)")
    months_to_complete: float = Field(..., description="Estimated months required to reach target")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations to reach target")
    risks: List[str] = Field(default_factory=list, description="Potential financial risks or bottlenecks")
    summary: str = Field(..., description="Executive summary of the goal feasibility evaluation")
