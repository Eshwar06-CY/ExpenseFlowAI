"""
Unit & Integration Tests for Financial Digital Twin & Simulation Engine - ExpenseFlowAI

Tests DigitalTwinService in-memory what-if simulations (Large Purchase, Salary Increase, Job Loss),
survival runway analysis, LLM fallback, router endpoints, and CRITICAL DB ISOLATION (0 DB mutations).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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
from app.services.digital_twin import DigitalTwinService
from app.services.cache import cache_service

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_digital_twin.db"
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
    user = db.query(User).filter(User.email == "twin_test@example.com").first()
    if not user:
        user = User(
            email="twin_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Digital Twin Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=200000.0)
        db.add(account)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=80000.0, date=now - timedelta(days=10))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=35000.0, date=now - timedelta(days=5))
        db.add_all([tx_inc, tx_exp])

        bill = Bill(user_id=user.id, name="Rent", amount=15000.0, due_date=now + timedelta(days=10), is_paid=False)
        goal = Goal(user_id=user.id, name="MacBook Goal", target_amount=120000.0, current_amount=40000.0)
        db.add_all([bill, goal])

        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service & Simulation Tests (With DB Isolation Checks)
# -------------------------------------------------------------------

def test_get_baseline_digital_twin_state():
    service = DigitalTwinService(provider=MagicMock())
    db = TestingSessionLocal()

    user = User(email="dt_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Main", type="checking", balance=50000.0)
    db.add(account)
    db.commit()

    state = service.get_baseline_twin_state(db=db, user_id=user.id)
    db.close()

    assert state["user_id"] == user.id
    assert state["total_balance"] == 50000.0
    assert "health_score" in state


def test_large_purchase_simulation_and_strict_db_isolation():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Simulation explanation: purchasing a bike reduces liquid reserves."

    service = DigitalTwinService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="dt_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Checking", type="checking", balance=200000.0)
    db.add(account)

    now = datetime.now()
    tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=80000.0, date=now - timedelta(days=10))
    tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=20000.0, date=now - timedelta(days=5))
    db.add_all([tx_inc, tx_exp])
    db.commit()
    cache_service.clear()

    # Pre-simulation DB state
    initial_balance_in_db = db.execute(select(Account.balance).where(Account.id == account.id)).scalar()
    initial_tx_count = db.query(Transaction).count()

    # Execute simulation (buy 150k bike)
    res = service.simulate_scenario(
        db=db,
        user_id=user.id,
        scenario_type="LARGE_PURCHASE",
        amount=150000.0,
        description="What if I buy a ₹1.5 lakh bike?"
    )

    # Verify simulation outputs
    assert res["impact"]["balance_before"] == 200000.0
    assert res["impact"]["balance_after"] == 50000.0
    assert res["financial_health_after"] <= res["financial_health_before"]

    # CRITICAL: Verify DB state post-simulation remains 100% UNCHANGED
    post_balance_in_db = db.execute(select(Account.balance).where(Account.id == account.id)).scalar()
    post_tx_count = db.query(Transaction).count()
    db.close()

    assert post_balance_in_db == initial_balance_in_db == 200000.0
    assert post_tx_count == initial_tx_count


def test_salary_increase_and_job_loss_simulations():
    service = DigitalTwinService(provider=MagicMock())
    db = TestingSessionLocal()

    user = User(email="dt_user3@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Savings", type="checking", balance=100000.0)
    db.add(account)

    now = datetime.now()
    tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=50000.0, date=now - timedelta(days=10))
    tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=20000.0, date=now - timedelta(days=5))
    db.add_all([tx_inc, tx_exp])
    db.commit()

    # Salary Increase (+20%)
    res_sal = service.simulate_scenario(
        db=db,
        user_id=user.id,
        scenario_type="SALARY_CHANGE",
        percentage_change=20.0
    )
    assert res_sal["impact"]["monthly_savings_after"] > res_sal["impact"]["monthly_savings_before"]

    # Job Loss (3 months)
    res_job = service.simulate_scenario(
        db=db,
        user_id=user.id,
        scenario_type="JOB_LOSS",
        duration_months=3
    )
    db.close()

    assert res_job["impact"]["monthly_savings_after"] < 0
    assert res_job["impact"]["survival_months"] > 0
    assert len(res_job["recommendations"]) >= 1


def test_digital_twin_llm_fallback():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("Provider offline")

    service = DigitalTwinService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="dt_user4@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    res = service.simulate_scenario(
        db=db,
        user_id=user.id,
        scenario_type="BONUS",
        amount=50000.0
    )
    db.close()

    assert "Under the" in res["explanation"]
    assert res["impact"]["balance_after"] > res["impact"]["balance_before"]


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_twin_endpoints_unauthenticated():
    assert client.get("/api/v1/ai/twin/state").status_code == 401
    assert client.post("/api/v1/ai/twin/simulate", json={"scenario_type": "LARGE_PURCHASE", "amount": 1000.0}).status_code == 401


def test_twin_endpoints_authenticated():
    headers = _get_auth_headers()

    # GET /twin/state
    resp_state = client.get("/api/v1/ai/twin/state", headers=headers)
    assert resp_state.status_code == 200
    data_state = resp_state.json()
    assert data_state["total_balance"] == 200000.0

    # POST /twin/simulate
    resp_sim = client.post(
        "/api/v1/ai/twin/simulate",
        headers=headers,
        json={
            "scenario_type": "LARGE_PURCHASE",
            "amount": 150000.0,
            "description": "What if I buy a ₹1.5 lakh bike?"
        }
    )

    assert resp_sim.status_code == 200
    data_sim = resp_sim.json()
    assert data_sim["scenario"] == "What if I buy a ₹1.5 lakh bike?"
    assert data_sim["impact"]["balance_after"] == 50000.0
    assert "explanation" in data_sim
