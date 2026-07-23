"""
Unit & Integration Tests for AI Financial Command Center Dashboard - ExpenseFlowAI

Tests the GET /api/v1/dashboard/overview unified aggregation endpoint, schema integrity,
health score trends, net worth calculations, digital twin preset generation, and bill timelines.
"""

from datetime import datetime, timedelta
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
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.services.cache import cache_service

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard_overview.db"
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
    cache_service.clear()
    previous_override = app.dependency_overrides.get(get_db)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        cache_service.clear()
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


def _get_auth_headers(email="command_center@example.com"):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash="fake_hashed_password",
            full_name="Command Center User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Primary Checking", type="checking", balance=150000.0)
        db.add(account)

        cat = Category(user_id=user.id, name="Dining Out", type="expense", icon="Utensils", color="#f43f5e")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=85000.0, date=now - timedelta(days=2))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, category_id=cat.id, type="expense", amount=25000.0, date=now - timedelta(days=1))
        db.add_all([tx_inc, tx_exp])

        budget = Budget(user_id=user.id, category_id=cat.id, amount=30000.0, spent=25000.0, month="2026-07")
        goal = Goal(user_id=user.id, name="MacBook Target", target_amount=200000.0, current_amount=120000.0)
        bill = Bill(user_id=user.id, name="Electric Bill", amount=1500.0, due_date=now + timedelta(days=1), is_paid=False)
        db.add_all([budget, goal, bill])

        db.commit()
        cache_service.clear()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}, user.id


# -------------------------------------------------------------------
# 1. Unauthenticated & Authorization Tests
# -------------------------------------------------------------------

def test_command_center_unauthenticated():
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


# -------------------------------------------------------------------
# 2. Unified Aggregation Endpoint Integration Tests
# -------------------------------------------------------------------

def test_command_center_overview_authenticated():
    headers, user_id = _get_auth_headers()
    response = client.get("/api/v1/dashboard/overview?period=30d", headers=headers)
    
    assert response.status_code == 200
    data = response.json()

    # Check top-level keys
    assert "financial_health" in data
    assert "metrics" in data
    assert "ai_executive_summary" in data
    assert "ai_insights_cards" in data
    assert "budget_overview" in data
    assert "goal_overview" in data
    assert "bills_timeline" in data
    assert "forecast_snapshot" in data
    assert "digital_twin_presets" in data

    # Check health score & metrics
    assert data["financial_health"]["score"] > 0
    assert data["metrics"]["total_balance"] == 150000.0
    assert data["metrics"]["period_income"] == 85000.0
    assert data["metrics"]["period_expense"] == 25000.0

    # Check digital twin simulation shortcuts
    presets = data["digital_twin_presets"]
    assert len(presets) >= 6
    assert any(p["id"] == "salary_increase" for p in presets)
    assert any(p["id"] == "unexpected_expense" for p in presets)


def test_command_center_root_alias_endpoint():
    headers, _ = _get_auth_headers("alias_test@example.com")
    response = client.get("/api/dashboard/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "ai_executive_summary" in data
