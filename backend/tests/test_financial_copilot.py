"""
Unit & Integration Tests for AI Financial Copilot Service - ExpenseFlowAI

Tests AIFinancialCopilotService orchestration, sub-service integration, LLM prompt assembly,
graceful error handling, and API endpoints GET /copilot/briefing and POST /copilot/briefing.
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
from app.models.bill import Bill
from app.models.goal import Goal
from app.services.financial_copilot import AIFinancialCopilotService

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_financial_copilot.db"
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
    user = db.query(User).filter(User.email == "copilot_test@example.com").first()
    if not user:
        user = User(
            email="copilot_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Copilot Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=25000.0)
        db.add(account)
        db.commit()

        # Add upcoming unpaid bill
        bill = Bill(
            user_id=user.id,
            name="Electricity Bill",
            amount=150.0,
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            is_paid=False
        )
        db.add(bill)

        # Add active goal
        goal = Goal(
            user_id=user.id,
            name="MacBook Fund",
            target_amount=100000.0,
            current_amount=80000.0
        )
        db.add(goal)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service Orchestration Tests
# -------------------------------------------------------------------

def test_copilot_service_orchestration_success():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = json.dumps({
        "greeting": "Good Morning 👋",
        "highlights": ["Stayed under budget yesterday", "MacBook Fund is 80% complete"],
        "alerts": ["Electricity Bill due in 3 days"],
        "recommendations": ["Automate monthly goal transfer", "Review category limits"],
        "encouragement": "You are making consistent progress. Keep it up!"
    })

    mock_coach = MagicMock()
    mock_coach.generate_coaching_report.return_value = {
        "strengths": ["Healthy savings rate"],
        "recommendations": ["Automate monthly savings"]
    }

    mock_anomaly = MagicMock()
    mock_anomaly.detect_anomalies.return_value = {
        "anomalies": [{"message": "Food spending spike detected."}]
    }

    service = AIFinancialCopilotService(
        provider=mock_provider,
        coach_service=mock_coach,
        anomaly_service=mock_anomaly
    )

    db = TestingSessionLocal()
    user = User(email="copilot_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    briefing = service.generate_daily_briefing(db=db, user_id=user.id, period="30d")
    db.close()

    assert briefing["greeting"] == "Good Morning 👋"
    assert briefing["health_score"] >= 0
    assert "Stayed under budget yesterday" in briefing["highlights"]
    assert briefing["encouragement"] == "You are making consistent progress. Keep it up!"


def test_copilot_service_graceful_fault_tolerance():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("LLM Offline")

    mock_coach = MagicMock()
    mock_coach.generate_coaching_report.side_effect = RuntimeError("Coach Failure")

    mock_anomaly = MagicMock()
    mock_anomaly.detect_anomalies.side_effect = RuntimeError("Anomaly Failure")

    service = AIFinancialCopilotService(
        provider=mock_provider,
        coach_service=mock_coach,
        anomaly_service=mock_anomaly
    )

    db = TestingSessionLocal()
    user = User(email="copilot_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    briefing = service.generate_daily_briefing(db=db, user_id=user.id, period="30d")
    db.close()

    assert briefing["greeting"] == "Good Morning 👋"
    assert "health_score" in briefing
    assert isinstance(briefing["highlights"], list)
    assert isinstance(briefing["recommendations"], list)


# -------------------------------------------------------------------
# 2. Router Endpoint Tests
# -------------------------------------------------------------------

def test_get_copilot_briefing_unauthenticated():
    response = client.get("/api/v1/ai/copilot/briefing")
    assert response.status_code == 401


@patch("app.services.financial_copilot.AIFinancialCopilotService.generate_daily_briefing")
def test_get_copilot_briefing_authenticated_success(mock_briefing):
    mock_briefing.return_value = {
        "greeting": "Good Morning 👋",
        "health_score": 92,
        "health_status": "Healthy",
        "highlights": ["Stayed under budget yesterday"],
        "alerts": ["Electricity bill due in 3 days"],
        "recommendations": ["Review spending limits"],
        "goal_updates": [{
            "goal_name": "MacBook Fund",
            "target_amount": 100000.0,
            "current_saved": 80000.0,
            "progress_pct": 80.0,
            "status": "ON_TRACK"
        }],
        "upcoming_events": [{
            "title": "Electricity Bill due",
            "type": "BILL",
            "amount": 150.0,
            "due_date": "2026-07-25",
            "days_remaining": 3
        }],
        "encouragement": "Great job building your wealth!"
    }

    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/copilot/briefing?period=30d", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["greeting"] == "Good Morning 👋"
    assert data["health_score"] == 92
    assert len(data["goal_updates"]) == 1
    assert data["goal_updates"][0]["goal_name"] == "MacBook Fund"


@patch("app.services.financial_copilot.AIFinancialCopilotService.generate_daily_briefing")
def test_post_copilot_briefing_success(mock_briefing):
    mock_briefing.return_value = {
        "greeting": "Good Morning 👋",
        "health_score": 90,
        "health_status": "Healthy",
        "highlights": ["Strong savings rate"],
        "alerts": [],
        "recommendations": ["Maintain current trajectory"],
        "goal_updates": [],
        "upcoming_events": [],
        "encouragement": "Keep up the fantastic momentum!"
    }

    headers = _get_auth_headers()
    response = client.post("/api/v1/ai/copilot/briefing", headers=headers, json={"period": "30d"})

    assert response.status_code == 200
    data = response.json()
    assert data["greeting"] == "Good Morning 👋"
    assert data["health_score"] == 90
