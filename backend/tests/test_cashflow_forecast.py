"""
Unit & Integration Tests for Predictive Cash Flow Engine - ExpenseFlowAI

Tests CashFlowForecastService calculation logic, 7/30/90-day balance projections,
confidence score boundaries, risk warnings, LLM fallback, and API endpoints.
"""

from datetime import datetime, timedelta, timezone
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
from app.models.bill import Bill
from app.models.goal import Goal
from app.services.cashflow_forecast import CashFlowForecastService

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cashflow_forecast.db"
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
    user = db.query(User).filter(User.email == "forecast_test@example.com").first()
    if not user:
        user = User(
            email="forecast_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Forecast Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=45000.0)
        db.add(account)

        # Add income and expense transactions
        now = datetime.now(timezone.utc)
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=60000.0, date=now - timedelta(days=10))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=25000.0, date=now - timedelta(days=5))
        db.add_all([tx_inc, tx_exp])

        # Add unpaid bill and goal
        bill = Bill(user_id=user.id, name="Electricity Bill", amount=1500.0, due_date=now + timedelta(days=15), is_paid=False)
        goal = Goal(user_id=user.id, name="Emergency Reserve", target_amount=100000.0, current_amount=20000.0)
        db.add_all([bill, goal])

        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service & Forecast Calculation Tests
# -------------------------------------------------------------------

def test_forecast_calculations_and_horizons():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Cashflow analysis: Expecting positive balance trajectory over 90 days."

    service = CashFlowForecastService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="fc_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Main", type="checking", balance=45000.0)
    db.add(account)
    db.commit()

    result = service.generate_forecast(db=db, user_id=user.id, period="30d")
    db.close()

    assert "forecast" in result
    assert len(result["forecast"]) == 3
    horizons = [item["days"] for item in result["forecast"]]
    assert horizons == [7, 30, 90]

    for item in result["forecast"]:
        assert "expected_balance" in item
        assert "net_change" in item
        assert "risk_events" in item

    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["warnings"], list)
    assert isinstance(result["opportunities"], list)
    assert len(result["explanation"]) > 0


def test_forecast_deterministic_fallback_on_llm_failure():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("Ollama Offline")

    service = CashFlowForecastService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="fc_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    result = service.generate_forecast(db=db, user_id=user.id, period="30d")
    db.close()

    assert len(result["forecast"]) == 3
    assert "Based on historical run rates" in result["explanation"]


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_get_forecast_unauthenticated():
    response = client.get("/api/v1/ai/forecast")
    assert response.status_code == 401


def test_get_forecast_authenticated_success():
    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/forecast?period=30d", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["forecast"]) == 3
    assert data["forecast"][0]["period_label"] == "7-Day"
    assert data["forecast"][1]["period_label"] == "30-Day"
    assert data["forecast"][2]["period_label"] == "90-Day"
    assert 0.0 <= data["confidence"] <= 1.0


def test_post_forecast_analyze_authenticated_success():
    headers = _get_auth_headers()
    response = client.post("/api/v1/ai/forecast/analyze", headers=headers, json={"period": "30d"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["forecast"]) == 3
    assert data["explanation"] is not None
