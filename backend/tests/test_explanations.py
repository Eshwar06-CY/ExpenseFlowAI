"""
Unit & Integration Tests for Explainable AI (XAI) Framework - ExpenseFlowAI
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
from app.services.cache import cache_service

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_explanations.db"
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


def _get_auth_headers(email="xai_user@example.com"):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash="fake_password_hash",
            full_name="Explainable AI User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=180000.0)
        db.add(account)

        cat = Category(user_id=user.id, name="Dining", type="expense")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=90000.0, date=now - timedelta(days=2))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, category_id=cat.id, type="expense", amount=22000.0, date=now - timedelta(days=1))
        db.add_all([tx_inc, tx_exp])

        budget = Budget(user_id=user.id, category_id=cat.id, amount=25000.0, spent=22000.0, month="2026-07")
        goal = Goal(user_id=user.id, name="Laptop Savings", target_amount=150000.0, current_amount=90000.0)
        db.add_all([budget, goal])
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}, user.id


def test_explanations_unauthenticated():
    response = client.get("/api/v1/explanations/dashboard/highest_expense")
    assert response.status_code == 401


def test_explanation_forecast():
    headers, user_id = _get_auth_headers()
    response = client.get("/api/v1/explanations/forecast/30d", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "explanation" in data
    exp = data["explanation"]
    assert exp["feature"] == "forecast"
    assert exp["confidence"] > 0.0
    assert len(exp["data_used"]) > 0
    assert len(exp["assumptions"]) > 0
    assert len(exp["limitations"]) > 0
    assert "current_balance" in exp["finance_engine_metrics"]


def test_explanation_budget():
    headers, user_id = _get_auth_headers("budget_xai@example.com")
    response = client.get("/api/v1/explanations/budget/1", headers=headers)
    assert response.status_code == 200
    data = response.json()

    exp = data["explanation"]
    assert exp["feature"] == "budget"
    assert exp["confidence"] >= 0.90
    assert len(exp["suggested_actions"]) > 0


def test_explanation_digital_twin():
    headers, user_id = _get_auth_headers("twin_xai@example.com")
    response = client.get("/api/v1/explanations/digital_twin/salary_increase", headers=headers)
    assert response.status_code == 200
    data = response.json()

    exp = data["explanation"]
    assert exp["feature"] == "digital_twin"
    assert "Digital Twin" in exp["reason"]
    assert "baseline_health_score" in exp["finance_engine_metrics"]


def test_explanation_notification():
    headers, user_id = _get_auth_headers("notif_xai@example.com")
    response = client.get("/api/v1/explanations/notification/1", headers=headers)
    assert response.status_code == 200
    data = response.json()

    exp = data["explanation"]
    assert exp["feature"] == "notification"
    assert exp["confidence"] >= 0.95
