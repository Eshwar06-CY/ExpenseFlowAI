"""
Unit & Integration Tests for Autonomous Workflow Engine - ExpenseFlowAI

Tests WorkflowEngine discovery, step ordering, retry logic, step rollbacks on failure,
progress tracking, and API endpoints GET /workflows and POST /workflows/run.
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
from app.models.goal import Goal
from app.workflows.engine import WorkflowEngine
from app.workflows.base import BaseWorkflow, WorkflowStep

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workflow_engine.db"
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
    user = db.query(User).filter(User.email == "wf_test@example.com").first()
    if not user:
        user = User(
            email="wf_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Workflow Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=30000.0)
        db.add(account)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Workflow Engine & Pipeline Tests
# -------------------------------------------------------------------

def test_workflow_engine_discovery():
    engine_svc = WorkflowEngine(provider=MagicMock())
    workflows = engine_svc.list_workflows()
    names = {w["name"] for w in workflows}
    assert "GoalWorkflow" in names
    assert "BudgetOptimizerWorkflow" in names
    assert "ExpenseReductionWorkflow" in names
    assert "SubscriptionCleanupWorkflow" in names
    assert "FinancialReviewWorkflow" in names


def test_goal_workflow_execution_success():
    engine_svc = WorkflowEngine(provider=MagicMock())
    db = TestingSessionLocal()
    user = User(email="wf_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    res = engine_svc.execute_workflow(
        db=db,
        user_id=user.id,
        workflow_name="GoalWorkflow",
        parameters={"goal_name": "Emergency Fund", "target_amount": 50000.0}
    )
    db.close()

    assert res["status"] == "COMPLETED"
    assert res["steps_completed"] == 4
    assert len(res["actions_taken"]) >= 2
    assert len(res["recommendations"]) >= 1


def test_workflow_retry_and_rollback_mechanics():
    db = TestingSessionLocal()
    user = User(email="wf_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    rollback_mock = MagicMock()

    class FailingWorkflow(BaseWorkflow):
        name = "FailingWorkflow"
        description = "Test Failing Workflow with Rollback"

        def _setup_steps(self):
            self.steps = [
                WorkflowStep("Step 1 Ok", self._step1, rollback_handler=rollback_mock),
                WorkflowStep("Step 2 Fails", self._step2, max_retries=1),
            ]

        def _step1(self, db, uid, ctx):
            return {"action": {"type": "STEP1"}}

        def _step2(self, db, uid, ctx):
            raise ValueError("Unrecoverable step error")

    wf = FailingWorkflow()
    res = wf.run(db=db, user_id=user.id)
    db.close()

    assert res["status"] == "ROLLED_BACK"
    assert res["steps_completed"] == 1
    assert rollback_mock.called


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_list_workflows_unauthenticated():
    response = client.get("/api/v1/ai/workflows")
    assert response.status_code == 401


def test_list_workflows_authenticated():
    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/workflows", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    names = {w["name"] for w in data}
    assert "ExpenseReductionWorkflow" in names


def test_run_workflow_api_authenticated():
    headers = _get_auth_headers()
    response = client.post(
        "/api/v1/ai/workflows/run",
        headers=headers,
        json={
            "workflow_name": "ExpenseReductionWorkflow",
            "period": "30d"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workflow"] == "ExpenseReductionWorkflow"
    assert data["status"] == "COMPLETED"
    assert data["steps_completed"] == 3
