"""
Pydantic Schemas for Financial Digital Twin & Simulation Engine - ExpenseFlowAI
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SimulationScenarioType(str, Enum):
    LARGE_PURCHASE = "LARGE_PURCHASE"
    SALARY_CHANGE = "SALARY_CHANGE"
    JOB_LOSS = "JOB_LOSS"
    BONUS = "BONUS"
    EXPENSE_INCREASE = "EXPENSE_INCREASE"
    CUSTOM = "CUSTOM"


class SimulationRequest(BaseModel):
    scenario_type: SimulationScenarioType = Field(..., description="Scenario type: LARGE_PURCHASE, SALARY_CHANGE, JOB_LOSS, BONUS, EXPENSE_INCREASE, CUSTOM", examples=["LARGE_PURCHASE"])
    amount: Optional[float] = Field(0.0, description="Monetary value for purchase, bonus, or bill change", examples=[150000.0])
    percentage_change: Optional[float] = Field(0.0, description="Percentage change e.g. +20.0 for 20% salary increase or -15.0 for reduction", examples=[20.0])
    duration_months: Optional[int] = Field(1, ge=1, le=60, description="Scenario duration horizon in months (default 1)", examples=[3])
    description: Optional[str] = Field(None, description="Custom prompt description of what-if scenario", examples=["What if I buy a ₹1.5 lakh bike?"])
    period: Optional[str] = Field("30d", description="Baseline analysis period e.g. 30d, 90d")


class FinancialImpactMetrics(BaseModel):
    balance_before: float = Field(..., description="Active balance before simulation")
    balance_after: float = Field(..., description="Simulated active balance after scenario")
    monthly_savings_before: float = Field(..., description="Monthly net savings before simulation")
    monthly_savings_after: float = Field(..., description="Simulated monthly net savings after scenario")
    reserve_months_before: float = Field(..., description="Emergency cash reserve in months before simulation")
    reserve_months_after: float = Field(..., description="Simulated emergency cash reserve in months after scenario")
    survival_months: float = Field(..., description="Estimated months financial state can survive under scenario")


class DigitalTwinStateResponse(BaseModel):
    user_id: int = Field(..., description="User ID")
    total_balance: float = Field(..., description="Total active balance")
    monthly_income: float = Field(..., description="Monthly income baseline")
    monthly_expenses: float = Field(..., description="Monthly expenses baseline")
    monthly_savings: float = Field(..., description="Monthly net savings baseline")
    health_score: int = Field(..., description="Baseline health score")
    health_status: str = Field(..., description="Baseline health rating status")
    active_goals_count: int = Field(..., description="Number of active financial goals")
    unpaid_bills_count: int = Field(..., description="Number of unpaid bills")


class DigitalTwinSimulationResponse(BaseModel):
    scenario: str = Field(..., description="Name / summary of simulated scenario")
    impact: FinancialImpactMetrics = Field(..., description="Detailed quantitative before vs after impact metrics")
    financial_health_before: int = Field(..., ge=0, le=100, description="Financial health score before scenario (0-100)")
    financial_health_after: int = Field(..., ge=0, le=100, description="Simulated financial health score after scenario (0-100)")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations based on scenario impact")
    explanation: str = Field(..., description="AI narrative explanation of scenario consequences and survival analysis")
