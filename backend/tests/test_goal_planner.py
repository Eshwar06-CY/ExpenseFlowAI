"""
Unit & Integration Tests for AI Goal Planner Service - ExpenseFlowAI

Tests AIGoalPlannerService, timeline calculations, LLM prompt formatting, fallback execution,
and API endpoints POST /ai/goals/plan and GET /ai/goals/evaluate.
"""

from datetime import datetime, timedelta, timezone
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.services.goal_planner import AIGoalPlannerService
from app.schemas.goals import GoalFeasibilityStatus

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_goal_planner.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database():
    previous_override = app.dependency_overrides.get(get_db)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


def _get_auth_headers():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "goal_test@example.com").first()
    if not user:
        user = User(
            email="goal_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Goal Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=50000.0)
        db.add(account)
        db.commit()

        # Add income to establish monthly surplus
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            type="income",
            amount=200000.0,
            date=datetime.now(timezone.utc) - timedelta(days=5)
        )
        db.add(tx)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service Tests (Mocked LLM & FinanceEngine integration)
# -------------------------------------------------------------------

def test_goal_already_achieved():
    mock_provider = MagicMock()
    service = AIGoalPlannerService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="achieved_user@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    report = service.evaluate_goal(
        db=db,
        user_id=user.id,
        goal_name="MacBook Pro",
        target_amount=100000.0,
        current_saved=100000.0
    )
    db.close()

    assert report["status"] == GoalFeasibilityStatus.ALREADY_ACHIEVED.value
    assert report["completion_probability"] == 1.0
    assert report["months_to_complete"] == 0.0


def test_goal_achievable_on_track():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = json.dumps({
        "status": "ON_TRACK",
        "completion_probability": 0.95,
        "recommendations": ["Set up automatic savings transfer of $10,000/mo"],
        "risks": ["Minor subscription creep"],
        "summary": "Goal is highly realistic based on current $200,000/mo surplus."
    })

    service = AIGoalPlannerService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="on_track_user@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Checking", type="checking", balance=10000.0)
    db.add(account)
    db.commit()

    tx = Transaction(user_id=user.id, account_id=account.id, type="income", amount=50000.0, date=datetime.now(timezone.utc) - timedelta(days=2))
    db.add(tx)
    db.commit()

    report = service.evaluate_goal(
        db=db,
        user_id=user.id,
        goal_name="iPhone 15",
        target_amount=80000.0,
        target_date="2027-01-01",
        current_saved=10000.0
    )
    db.close()

    assert report["status"] == GoalFeasibilityStatus.ON_TRACK.value
    assert report["completion_probability"] == 0.95
    assert len(report["recommendations"]) >= 1


def test_goal_unfeasible_zero_surplus():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("LLM Offline")

    service = AIGoalPlannerService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="unfeasible_user@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # User with zero income and zero surplus
    report = service.evaluate_goal(
        db=db,
        user_id=user.id,
        goal_name="Europe Trip",
        target_amount=120000.0,
        current_saved=0.0
    )
    db.close()

    assert report["status"] == GoalFeasibilityStatus.UNFEASIBLE.value
    assert report["completion_probability"] == 0.05
    assert "surplus" in report["summary"]


# -------------------------------------------------------------------
# 2. Router Endpoint Tests
# -------------------------------------------------------------------

def test_post_plan_goal_unauthenticated():
    response = client.post("/api/v1/ai/goals/plan", json={"goal_name": "Bike", "target_amount": 50000.0})
    assert response.status_code == 401


@patch("app.services.goal_planner.AIGoalPlannerService.evaluate_goal")
def test_post_plan_goal_authenticated_success(mock_evaluate):
    mock_evaluate.return_value = {
        "goal_name": "MacBook Pro",
        "target_amount": 180000.0,
        "current_saved": 20000.0,
        "monthly_required": 16000.0,
        "monthly_surplus": 25000.0,
        "status": GoalFeasibilityStatus.ON_TRACK.value,
        "completion_probability": 0.92,
        "estimated_completion_date": "2027-02-10",
        "months_to_complete": 6.4,
        "recommendations": ["Automate $16,000 monthly goal transfer"],
        "risks": ["Unexpected large repair bills"],
        "summary": "Your target is realistic and on track."
    }

    headers = _get_auth_headers()
    response = client.post(
        "/api/v1/ai/goals/plan",
        headers=headers,
        json={
            "goal_name": "MacBook Pro",
            "target_amount": 180000.0,
            "target_date": "2027-03-01",
            "current_saved": 20000.0
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["goal_name"] == "MacBook Pro"
    assert data["status"] == "ON_TRACK"
    assert data["completion_probability"] == 0.92


def test_get_evaluate_all_saved_user_goals_success():
    headers = _get_auth_headers()

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "goal_test@example.com").first()

    # Save a Goal object in database
    goal_item = Goal(
        user_id=user.id,
        name="Emergency Savings",
        target_amount=500000.0,
        current_amount=50000.0
    )
    db.add(goal_item)
    db.commit()
    db.close()

    response = client.get("/api/v1/ai/goals/evaluate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["goal_name"] == "Emergency Savings"
