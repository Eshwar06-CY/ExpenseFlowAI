"""
Unit & Integration Tests for AI Personal Finance Operating System (Financial OS) - ExpenseFlowAI

Tests AIFinancialOSService master orchestration, sub-service aggregation,
prioritization capping (Max 3 items/section), deterministic fallback execution,
and API endpoints GET /os/overview and POST /os/overview.
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
from app.services.financial_os import AIFinancialOSService

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_financial_os.db"
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
    user = db.query(User).filter(User.email == "os_test@example.com").first()
    if not user:
        user = User(
            email="os_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Financial OS Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=15000.0)
        db.add(account)

        bill = Bill(user_id=user.id, name="Internet Bill", amount=80.0, due_date=datetime.now(timezone.utc), is_paid=False)
        db.add(bill)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Master Orchestration & Service Tests
# -------------------------------------------------------------------

def test_financial_os_master_orchestration_success():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = json.dumps({
        "priorities": ["Pay electricity bill tomorrow", "Dining budget nearly exhausted", "Emergency fund on track"],
        "opportunities": ["Automate $500 monthly transfer", "Review unused subscriptions", "Invest surplus cash"],
        "alerts": ["Dining spending spike +42%"],
        "predictions": ["Estimated cash reserve trajectory: 5.2 months"],
        "motivation": "You are taking proactive control of your financial destiny!"
    })

    mock_coach = MagicMock()
    mock_coach.generate_coaching_report.return_value = {"strengths": ["Healthy savings rate"]}

    mock_anomaly = MagicMock()
    mock_anomaly.detect_anomalies.return_value = {"anomalies": [{"message": "Dining spike"}]}

    service = AIFinancialOSService(
        provider=mock_provider,
        coach_service=mock_coach,
        anomaly_service=mock_anomaly
    )

    db = TestingSessionLocal()
    user = User(email="os_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    overview = service.get_operating_system_overview(db=db, user_id=user.id, period="30d")
    db.close()

    assert "today" in overview
    assert len(overview["priorities"]) <= 3
    assert len(overview["opportunities"]) <= 3
    assert len(overview["alerts"]) <= 3
    assert len(overview["actions"]) <= 3
    assert overview["motivation"] == "You are taking proactive control of your financial destiny!"


def test_financial_os_prioritization_caps_max_three():
    mock_provider = MagicMock()
    # Provide 5 priorities & opportunities to test strict filtering cap (<=3)
    mock_provider.generate.return_value = json.dumps({
        "priorities": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
        "opportunities": ["Opp 1", "Opp 2", "Opp 3", "Opp 4"],
        "alerts": ["Alert 1", "Alert 2", "Alert 3", "Alert 4"],
        "predictions": ["Pred 1"],
        "motivation": "Keep going!"
    })

    service = AIFinancialOSService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="os_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    overview = service.get_operating_system_overview(db=db, user_id=user.id, period="30d")
    db.close()

    assert len(overview["priorities"]) == 3
    assert len(overview["opportunities"]) == 3
    assert len(overview["alerts"]) == 3


def test_financial_os_deterministic_fallback():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("LLM Offline")

    service = AIFinancialOSService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="os_user3@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    overview = service.get_operating_system_overview(db=db, user_id=user.id, period="30d")
    db.close()

    assert "today" in overview
    assert isinstance(overview["priorities"], list)
    assert isinstance(overview["actions"], list)
    assert "motivation" in overview


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_get_financial_os_overview_unauthenticated():
    response = client.get("/api/v1/ai/os/overview")
    assert response.status_code == 401


@patch("app.services.financial_os.AIFinancialOSService.get_operating_system_overview")
def test_get_financial_os_overview_authenticated_success(mock_overview):
    mock_overview.return_value = {
        "today": {
            "health_score": 92,
            "health_status": "Healthy",
            "total_balance": 15000.0,
            "period_income": 5000.0,
            "period_expense": 2000.0,
            "monthly_surplus": 3000.0
        },
        "priorities": ["Pay electricity bill tomorrow", "Dining budget nearly exhausted"],
        "opportunities": ["Automate $500 monthly transfer"],
        "alerts": ["Dining spending spike +42%"],
        "predictions": ["Estimated cash reserve trajectory: 5.2 months"],
        "actions": [{
            "title": "Schedule reminder for Internet Bill",
            "tool_name": "ReminderTool",
            "action": "create_reminder",
            "parameters": {"title": "Internet Bill", "amount": 80.0},
            "impact_description": "Ensures on-time payment."
        }],
        "motivation": "You are taking proactive control of your financial destiny!"
    }

    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/os/overview?period=30d", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["today"]["health_score"] == 92
    assert len(data["priorities"]) <= 3
    assert data["actions"][0]["tool_name"] == "ReminderTool"


@patch("app.services.financial_os.AIFinancialOSService.get_operating_system_overview")
def test_post_financial_os_overview_success(mock_overview):
    mock_overview.return_value = {
        "today": {
            "health_score": 85,
            "health_status": "Healthy",
            "total_balance": 10000.0,
            "period_income": 4000.0,
            "period_expense": 1500.0,
            "monthly_surplus": 2500.0
        },
        "priorities": ["Maintain healthy balance"],
        "opportunities": [],
        "alerts": [],
        "predictions": [],
        "actions": [],
        "motivation": "Keep up the momentum!"
    }

    headers = _get_auth_headers()
    response = client.post("/api/v1/ai/os/overview", headers=headers, json={"period": "30d"})

    assert response.status_code == 200
    data = response.json()
    assert data["today"]["health_score"] == 85
