"""
Unit & Integration Tests for AI Financial Coach Service - ExpenseFlowAI

Tests AIFinancialCoachService, JSON parsing, fallback logic, and API endpoints
GET /api/v1/ai/coach and POST /api/v1/ai/coach/analyze with mock providers.
"""

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
from app.services.ai_financial_coach import AIFinancialCoachService

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_coach.db"
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
    user = db.query(User).filter(User.email == "coach_test@example.com").first()
    if not user:
        user = User(
            email="coach_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Coach Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=10000.0)
        db.add(account)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service Tests (Mocked LLM)
# -------------------------------------------------------------------

def test_coach_service_generate_coaching_report_json_success():
    mock_provider = MagicMock()
    mock_response_json = {
        "summary": "Your financial foundation is solid with strong cash reserves.",
        "strengths": ["Savings rate of 50% is impressive", "Emergency fund covers 6 months"],
        "risks": ["Discretionary spending increased by 5%"],
        "recommendations": ["Automate $500 monthly goal transfer", "Review recurring bills"],
        "next_month_focus": ["Cap dining out at $300", "Maintain bill payment streak"],
        "encouragement": "Fantastic job building your savings buffer!"
    }
    mock_provider.generate.return_value = json.dumps(mock_response_json)

    service = AIFinancialCoachService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="coach_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    report = service.generate_coaching_report(db=db, user_id=user.id, period="30d")
    db.close()

    assert report["summary"] == "Your financial foundation is solid with strong cash reserves."
    assert "Savings rate of 50% is impressive" in report["strengths"]
    assert report["confidence"] == 0.95
    assert "income" in report["financial_snapshot"]


def test_coach_service_fallback_on_invalid_json():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Sorry, I am unable to format as JSON right now."

    service = AIFinancialCoachService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="coach_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    report = service.generate_coaching_report(db=db, user_id=user.id, period="30d")
    db.close()

    assert "summary" in report
    assert isinstance(report["strengths"], list)
    assert isinstance(report["recommendations"], list)
    assert report["confidence"] == 0.90  # Fallback confidence score


# -------------------------------------------------------------------
# 2. Router Endpoint Tests
# -------------------------------------------------------------------

def test_get_financial_coaching_unauthenticated():
    response = client.get("/api/v1/ai/coach")
    assert response.status_code == 401


@patch("app.services.ai_financial_coach.AIFinancialCoachService.generate_coaching_report")
def test_get_financial_coaching_authenticated_success(mock_report):
    mock_report.return_value = {
        "summary": "Solid financial standing.",
        "financial_snapshot": {
            "income": 5000.0,
            "expenses": 2000.0,
            "savings": 3000.0,
            "savings_rate": 60.0,
            "health_score": 85,
            "health_status": "Healthy",
            "reserve_months": 5.0,
            "budget_adherence_pct": 95.0,
            "bill_reliability_pct": 100.0
        },
        "strengths": ["60% savings rate"],
        "risks": ["Minor subscription creep"],
        "recommendations": ["Maintain current trajectory"],
        "next_month_focus": ["Review recurring bills"],
        "encouragement": "Keep it up!",
        "confidence": 0.95
    }

    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/coach?period=30d", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Solid financial standing."
    assert data["financial_snapshot"]["income"] == 5000.0
    assert data["strengths"] == ["60% savings rate"]


@patch("app.services.ai_financial_coach.AIFinancialCoachService.generate_coaching_report")
def test_post_analyze_coaching_success(mock_report):
    mock_report.return_value = {
        "summary": "Focused coaching assessment for savings.",
        "financial_snapshot": {
            "income": 5000.0,
            "expenses": 2000.0,
            "savings": 3000.0,
            "savings_rate": 60.0,
            "health_score": 85,
            "health_status": "Healthy",
            "reserve_months": 5.0,
            "budget_adherence_pct": 95.0,
            "bill_reliability_pct": 100.0
        },
        "strengths": ["High savings margin"],
        "risks": [],
        "recommendations": ["Invest surplus savings"],
        "next_month_focus": ["Open high yield savings"],
        "encouragement": "Great job!",
        "confidence": 0.95
    }

    headers = _get_auth_headers()
    response = client.post(
        "/api/v1/ai/coach/analyze",
        headers=headers,
        json={"period": "30d", "focus_area": "savings"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Focused coaching assessment for savings."
    assert data["recommendations"] == ["Invest surplus savings"]
