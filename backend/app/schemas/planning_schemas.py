from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # 'salary_increase', 'spend_reduction', 'rent_increase', 'one_off_purchase'
    amount: float = 0.0
    category_id: Optional[int] = None
    percent_change: Optional[float] = None
    one_off_date: Optional[datetime] = None
    is_active: bool = True

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    percent_change: Optional[float] = None
    one_off_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ScenarioResponse(ScenarioBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class ForecastTimelinePoint(BaseModel):
    date: str
    balance: float

class ForecastResponse(BaseModel):
    balance_7d: float
    balance_30d: float
    balance_90d: float
    monthly_surplus: float
    timeline: List[ForecastTimelinePoint]

class ProgressTimelinePoint(BaseModel):
    date: str
    expected_amount: float

class SavingsPlanResponse(BaseModel):
    target_amount: float
    current_amount: float
    remaining_amount: float
    required_monthly_savings: float
    estimated_completion_date: Optional[str] = None
    progress_timeline: List[ProgressTimelinePoint]

class BudgetRecommendationRow(BaseModel):
    category_id: int
    category_name: str
    avg_monthly_spending: float
    recommended_budget: float
    current_budget: Optional[float] = None
    status: str  # 'overspending_risk', 'underspending_opportunity', 'aligned'

class HealthTrendPoint(BaseModel):
    month: str
    score: int

class FinancialHealthResponse(BaseModel):
    health_score: int
    savings_rate: float
    expense_ratio: float
    income_stability: float
    emergency_fund_coverage_months: float
    budget_adherence_rate: float
    cash_reserve: float
    historical_health_trend: List[HealthTrendPoint]

class TimelineItem(BaseModel):
    date: str
    type: str  # 'transaction_income', 'transaction_expense', 'bill', 'goal_milestone', 'recurring_event', 'budget_reset', 'forecast_event'
    title: str
    description: str
    amount: float
