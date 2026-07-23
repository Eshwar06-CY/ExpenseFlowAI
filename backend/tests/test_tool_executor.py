"""
Unit & Integration Tests for AI Tool Registry & Executor - ExpenseFlowAI

Tests ToolRegistry, ToolExecutor intent routing, parameter validation,
safety confirmation flow for destructive actions, and API endpoint POST /api/v1/ai/action.
"""

from datetime import datetime, timezone
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
from app.ai.tool_registry import ToolRegistry, BudgetTool, GoalTool, ExpenseTool, ReminderTool
from app.ai.tool_executor import ToolExecutor
from app.schemas.tools import ToolExecutionStatus

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tool_executor.db"
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
    user = db.query(User).filter(User.email == "tool_test@example.com").first()
    if not user:
        user = User(
            email="tool_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Tool Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=50000.0)
        db.add(account)

        # Add subscription for deletion tests
        bill = Bill(user_id=user.id, name="Netflix", amount=15.99, due_date=datetime.now(timezone.utc), is_paid=False)
        db.add(bill)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. ToolRegistry & Execution Tests
# -------------------------------------------------------------------

def test_tool_registry_discovery():
    tools = ToolRegistry.list_tools()
    tool_names = {t["name"] for t in tools}
    assert "BudgetTool" in tool_names
    assert "GoalTool" in tool_names
    assert "ExpenseTool" in tool_names
    assert "ReminderTool" in tool_names
    assert "ReportTool" in tool_names


def test_executor_budget_creation_intent():
    executor = ToolExecutor(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="tool_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    res = executor.execute_action(
        db=db,
        user_id=user.id,
        message="Create a grocery budget of 7000"
    )
    db.close()

    assert res["status"] == ToolExecutionStatus.SUCCESS.value
    assert res["tool"] == "BudgetTool"
    assert res["result"]["amount"] == 7000.0
    assert res["result"]["category"] in ["Grocery", "Groceries"]


def test_executor_destructive_action_confirmation_required():
    executor = ToolExecutor(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="tool_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # Step 1: Attempt delete without confirmed=True -> Should return REQUIRES_CONFIRMATION
    res1 = executor.execute_action(
        db=db,
        user_id=user.id,
        message="Delete my Netflix subscription",
        confirmed=False
    )
    assert res1["status"] == ToolExecutionStatus.REQUIRES_CONFIRMATION.value
    assert res1["confirmation_prompt"] is not None

    # Step 2: Pass confirmed=True -> Executes tool deletion
    bill = Bill(user_id=user.id, name="Netflix", amount=15.99, due_date=datetime.now(timezone.utc), is_paid=False)
    db.add(bill)
    db.commit()

    res2 = executor.execute_action(
        db=db,
        user_id=user.id,
        message="Delete my Netflix subscription",
        tool_name="ExpenseTool",
        action="delete_subscription",
        parameters={"subscription_name": "Netflix"},
        confirmed=True
    )
    db.close()

    assert res2["status"] == ToolExecutionStatus.SUCCESS.value
    assert res2["result"]["deleted_name"] == "Netflix"


def test_executor_invalid_tool_handling():
    executor = ToolExecutor(provider=MagicMock())
    db = TestingSessionLocal()
    res = executor.execute_action(
        db=db,
        user_id=1,
        tool_name="NonExistentTool",
        action="fake_action"
    )
    db.close()

    assert res["status"] == ToolExecutionStatus.INVALID_TOOL.value


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_post_action_unauthenticated():
    response = client.post("/api/v1/ai/action", json={"message": "Create a budget"})
    assert response.status_code == 401


def test_post_action_authenticated_success():
    headers = _get_auth_headers()
    response = client.post(
        "/api/v1/ai/action",
        headers=headers,
        json={
            "message": "Set a reminder to pay rent 15000",
            "confirmed": False
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "ReminderTool"
    assert data["status"] == "SUCCESS"
    assert data["result"]["amount"] == 15000.0
