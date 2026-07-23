"""
Unit & Integration Tests for AI Financial Strategy Planner - ExpenseFlowAI

Tests AIStrategyPlannerService roadmap generation (1Y/3Y/5Y), top 5 priorities,
12-month action checklist, confidence score, LLM fallback, and API endpoints.
"""

from datetime import datetime, timedelta
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
from app.services.strategy_planner import AIStrategyPlannerService
from app.services.cache import cache_service

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_strategy_planner.db"
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


def _get_auth_headers():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "strat_test@example.com").first()
    if not user:
        user = User(
            email="strat_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Strategy Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=150000.0)
        db.add(account)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=60000.0, date=now - timedelta(days=10))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=25000.0, date=now - timedelta(days=5))
        db.add_all([tx_inc, tx_exp])

        bill = Bill(user_id=user.id, name="Credit Card Bill", amount=12000.0, due_date=now + timedelta(days=12), is_paid=False)
        goal = Goal(user_id=user.id, name="Emergency Fund", target_amount=100000.0, current_amount=30000.0)
        db.add_all([bill, goal])

        db.commit()
        cache_service.clear()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service & Roadmap Calculation Tests
# -------------------------------------------------------------------

def test_strategy_planner_roadmap_generation():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = '{"priorities": ["P1", "P2", "P3", "P4", "P5"], "one_year_plan": ["Y1"], "three_year_plan": ["Y3"], "five_year_plan": ["Y5"]}'

    service = AIStrategyPlannerService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="st_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Checking", type="checking", balance=100000.0)
    db.add(account)

    now = datetime.now()
    tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=60000.0, date=now - timedelta(days=10))
    tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=25000.0, date=now - timedelta(days=5))
    db.add_all([tx_inc, tx_exp])
    db.commit()
    cache_service.clear()

    result = service.generate_strategy_plan(db=db, user_id=user.id, period="30d")
    db.close()

    assert "current_health" in result
    assert 0 <= result["current_health"] <= 100
    assert len(result["priorities"]) == 5
    assert len(result["one_year_plan"]) >= 1
    assert len(result["three_year_plan"]) >= 1
    assert len(result["five_year_plan"]) >= 1
    assert len(result["monthly_actions"]) == 12
    assert 0.0 <= result["confidence"] <= 1.0


def test_strategy_planner_deterministic_fallback():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("Ollama provider offline")

    service = AIStrategyPlannerService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="st_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    result = service.generate_strategy_plan(db=db, user_id=user.id, period="30d")
    db.close()

    assert len(result["priorities"]) == 5
    assert len(result["monthly_actions"]) == 12
    assert result["confidence"] >= 0.70


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_strategy_endpoints_unauthenticated():
    assert client.get("/api/v1/ai/strategy").status_code == 401
    assert client.post("/api/v1/ai/strategy/generate", json={"period": "30d"}).status_code == 401


def test_strategy_endpoints_authenticated():
    headers = _get_auth_headers()

    # GET /strategy
    resp_get = client.get("/api/v1/ai/strategy?period=30d", headers=headers)
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert len(data_get["priorities"]) == 5
    assert len(data_get["monthly_actions"]) == 12

    # POST /strategy/generate
    resp_post = client.post("/api/v1/ai/strategy/generate", headers=headers, json={"period": "30d"})
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["current_health"] >= 0
    assert len(data_post["one_year_plan"]) >= 1
