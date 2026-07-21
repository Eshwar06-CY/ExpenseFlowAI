from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.session import get_db
from app.models.user import User
from app.models.scenario import Scenario
from app.models.goal import Goal
from app.routers.deps import get_current_user
from app.services.planning_service import PlanningService
from app.schemas.planning_schemas import (
    ScenarioCreate, ScenarioUpdate, ScenarioResponse,
    ForecastResponse, SavingsPlanResponse, BudgetRecommendationRow,
    FinancialHealthResponse, TimelineItem
)
from app.services.cache import cache_service

router = APIRouter()

# --- Cash Flow Projections ---
@router.get("/forecast", response_model=ForecastResponse)
def get_cash_flow_forecast(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exposes 7/30/90-day cash flow projections including recurring schedules and What-If scenario simulations.
    """
    return PlanningService.calculate_forecasts(db, current_user.id)


# --- What-If Scenarios CRUD ---
@router.get("/scenarios", response_model=List[ScenarioResponse])
def get_user_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists saved What-If planning scenarios.
    """
    stmt = select(Scenario).where(Scenario.user_id == current_user.id)
    return db.execute(stmt).scalars().all()


@router.post("/scenarios", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Saves a new What-If planning scenario and invalidates forecast caches.
    """
    scenario = Scenario(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        type=payload.type,
        amount=payload.amount,
        category_id=payload.category_id,
        percent_change=payload.percent_change,
        one_off_date=payload.one_off_date,
        is_active=payload.is_active
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    # Invalidate forecast caches
    cache_service.delete(f"user:{current_user.id}:forecast:90")
    return scenario


@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates configuration variables of a saved What-If planning scenario.
    """
    stmt = select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == current_user.id)
    scenario = db.execute(stmt).scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Planning scenario not found.")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(scenario, k, v)

    db.commit()
    db.refresh(scenario)

    # Invalidate forecast caches
    cache_service.delete(f"user:{current_user.id}:forecast:90")
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Removes a What-If planning scenario.
    """
    stmt = select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == current_user.id)
    scenario = db.execute(stmt).scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Planning scenario not found.")

    db.delete(scenario)
    db.commit()

    # Invalidate forecast caches
    cache_service.delete(f"user:{current_user.id}:forecast:90")
    return Response(status_code=status.HTTP_244_NO_CONTENT) if hasattr(status, 'HTTP_244_NO_CONTENT') else Response(status_code=204)


# --- Savings Planner Contribution Math ---
@router.get("/savings/{goal_id}/plan", response_model=SavingsPlanResponse)
def get_savings_goal_calculations(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates monthly contribution suggestions, ETA, and progress timeline maps.
    """
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    goal = db.execute(stmt).scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found.")

    return PlanningService.calculate_savings_plan(db, goal)


# --- Budget Recommendations ---
@router.get("/budget-recommendations", response_model=List[BudgetRecommendationRow])
def get_category_budget_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Suggests category budgets, overspending alerts, and budget reset details.
    """
    return PlanningService.get_budget_recommendations(db, current_user.id)


# --- Financial Health Audits ---
@router.get("/financial-health", response_model=FinancialHealthResponse)
def get_financial_health_dash(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates composite financial health scores, coverage indices, and standard deviations.
    """
    return PlanningService.calculate_health_metrics(db, current_user.id)


# --- Chronological Timeline ---
@router.get("/timeline", response_model=List[TimelineItem])
def get_chronological_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves chronological financial timeline (transactions, due dates of bills, target milestones of savings goals, and upcoming recurring runs).
    """
    return PlanningService.get_financial_timeline(db, current_user.id)
