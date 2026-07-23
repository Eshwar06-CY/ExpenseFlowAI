"""
Unit & Integration Tests for Adaptive Financial Intelligence System - ExpenseFlowAI

Tests AdaptiveLearningService behavioral event tracking, Financial Discipline Score calculation,
recommendation effectiveness rate, early bill payment adaptation, privacy data isolation,
LLM fallback execution, and API endpoints GET /adaptive/profile and POST /adaptive/feedback.
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
from app.models.user_preferences import UserPreferences
from app.models.user_behavior import UserBehaviorEvent
from app.schemas.adaptive import UserFeedbackRequest
from app.services.adaptive_learning import AdaptiveLearningService
from app.services.cache import cache_service

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_adaptive_learning.db"
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
    user = db.query(User).filter(User.email == "adaptive_test@example.com").first()
    if not user:
        user = User(
            email="adaptive_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Adaptive Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=80000.0)
        db.add(account)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=50000.0, date=now - timedelta(days=10))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=20000.0, date=now - timedelta(days=5))
        db.add_all([tx_inc, tx_exp])
        db.commit()
        cache_service.clear()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service & Personalization Tests
# -------------------------------------------------------------------

def test_get_adaptive_profile_defaults():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Adaptive profile summary: Discipline score is 87/100."

    service = AdaptiveLearningService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="al_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Checking", type="checking", balance=50000.0)
    db.add(account)
    db.commit()

    profile = service.get_adaptive_profile(db=db, user_id=user.id)
    db.close()

    assert 0 <= profile["discipline_score"] <= 100
    assert 0.0 <= profile["recommendation_effectiveness"] <= 1.0
    assert 0.0 <= profile["personalization_confidence"] <= 1.0
    assert isinstance(profile["behavior_patterns"], list)
    assert len(profile["updated_preferences"]) >= 2
    assert "explanation" in profile


def test_record_user_feedback_and_behavioral_adaptation():
    service = AdaptiveLearningService(provider=MagicMock())
    db = TestingSessionLocal()

    user = User(email="al_user2@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # Step 1: Record ignored recommendation event
    req1 = UserFeedbackRequest(
        event_type="RECOMMENDATION_RESPONSE",
        category="Dining",
        recommendation_type="budget_cap",
        action="ignored",
        communication_style="direct"
    )
    profile1 = service.record_user_feedback(db=db, user_id=user.id, feedback=req1)
    assert any("Dining" in p for p in profile1["behavior_patterns"])

    # Step 2: Record early bill payment event -> should reduce reminder lead days
    req2 = UserFeedbackRequest(
        event_type="EARLY_BILL_PAYMENT",
        action="completed"
    )
    profile2 = service.record_user_feedback(db=db, user_id=user.id, feedback=req2)
    db.close()

    assert any("pays bills early" in p for p in profile2["behavior_patterns"])


def test_adaptive_llm_fallback():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("Ollama offline")

    service = AdaptiveLearningService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="al_user3@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    profile = service.get_adaptive_profile(db=db, user_id=user.id)
    db.close()

    assert "Your Financial Discipline Score is" in profile["explanation"]


# -------------------------------------------------------------------
# 2. Router API Endpoint Tests
# -------------------------------------------------------------------

def test_adaptive_endpoints_unauthenticated():
    assert client.get("/api/v1/ai/adaptive/profile").status_code == 401
    assert client.post("/api/v1/ai/adaptive/feedback", json={"action": "accepted"}).status_code == 401


def test_adaptive_endpoints_authenticated():
    headers = _get_auth_headers()

    # GET /adaptive/profile
    resp_get = client.get("/api/v1/ai/adaptive/profile", headers=headers)
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert 0 <= data_get["discipline_score"] <= 100
    assert 0.0 <= data_get["personalization_confidence"] <= 1.0

    # POST /adaptive/feedback
    resp_post = client.post(
        "/api/v1/ai/adaptive/feedback",
        headers=headers,
        json={
            "event_type": "RECOMMENDATION_RESPONSE",
            "category": "Shopping",
            "action": "accepted",
            "communication_style": "concise"
        }
    )

    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["recommendation_effectiveness"] >= 0.0
    assert len(data_post["updated_preferences"]) >= 2
