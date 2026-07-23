"""
Unit & Integration Tests for Multi-Agent System & AgentRouter - ExpenseFlowAI

Tests AgentRouter intent classification, single/multi-agent co-execution,
response merging, forced agent dispatching, error handling, and API endpoints.
"""

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
from app.agents.router import AgentRouter

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agent_router.db"
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
    user = db.query(User).filter(User.email == "agent_test@example.com").first()
    if not user:
        user = User(
            email="agent_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Agent Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=20000.0)
        db.add(account)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Router & Multi-Agent Co-Execution Tests
# -------------------------------------------------------------------

def test_agent_router_discovery():
    router = AgentRouter(provider=MagicMock())
    agents = router.list_agents()
    names = {a["name"] for a in agents}
    assert "FinancialCoachAgent" in names
    assert "GoalPlannerAgent" in names
    assert "BudgetAgent" in names
    assert "InvestmentAgent" in names
    assert "SubscriptionAgent" in names
    assert "TaxAgent" in names
    assert "DebtAgent" in names
    assert "ReportAgent" in names


def test_agent_router_single_agent_dispatch():
    router = AgentRouter(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="agent_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    res = router.route_and_execute(
        db=db,
        user_id=user.id,
        message="Create a category budget for groceries"
    )
    db.close()

    assert "BudgetAgent" in res["dispatched_agents"]
    assert len(res["agent_results"]) == 1
    assert res["agent_results"][0]["agent_name"] == "BudgetAgent"


def test_agent_router_multi_agent_dispatch_and_merge():
    router = AgentRouter(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="agent_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # Query triggering both GoalPlannerAgent and DebtAgent
    res = router.route_and_execute(
        db=db,
        user_id=user.id,
        message="I want to save $80,000 while paying off my credit card debt."
    )
    db.close()

    dispatched = set(res["dispatched_agents"])
    assert "GoalPlannerAgent" in dispatched
    assert "DebtAgent" in dispatched
    assert len(res["agent_results"]) >= 2
    assert "Multi-Agent Synthesis:" in res["merged_response"]


def test_agent_router_forced_agent_dispatch():
    router = AgentRouter(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="agent_user3@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    res = router.route_and_execute(
        db=db,
        user_id=user.id,
        message="How are my taxes and investments?",
        forced_agents=["TaxAgent", "InvestmentAgent"]
    )
    db.close()

    assert res["dispatched_agents"] == ["TaxAgent", "InvestmentAgent"]
    assert len(res["agent_results"]) == 2


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_list_agents_unauthenticated():
    response = client.get("/api/v1/ai/agents")
    assert response.status_code == 401


def test_list_agents_authenticated():
    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/agents", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8
    names = {a["name"] for a in data}
    assert "GoalPlannerAgent" in names
    assert "DebtAgent" in names


def test_dispatch_agents_api_authenticated():
    headers = _get_auth_headers()
    response = client.post(
        "/api/v1/ai/agents/dispatch",
        headers=headers,
        json={
            "message": "Audit my subscriptions and generate a report",
            "period": "30d"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "SubscriptionAgent" in data["dispatched_agents"] or "ReportAgent" in data["dispatched_agents"]
    assert len(data["agent_results"]) >= 1
    assert data["merged_response"] is not None
