"""
Unit & Integration Tests for Personalization & Privacy Center - ExpenseFlowAI

Tests authentication, authorization, GET /api/personalization overview,
PUT /api/personalization/preferences, DELETE /api/personalization/behavior/{id},
POST /api/personalization/reset ("Forget Everything"), and GET /api/personalization/export.
"""

from datetime import datetime
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.personalization import AIPersonalizationSettings
from app.models.user_behavior import UserLearnedBehavior, UserBehaviorEvent
from app.services.personalization_service import PersonalizationService
from app.services.privacy_service import PrivacyService
from app.services.cache import cache_service

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_personalization.db"
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


def _get_auth_headers(email="p_user1@example.com"):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash="fake_hashed_password",
            full_name="Personalization User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}, user.id


# -------------------------------------------------------------------
# 1. Unauthenticated & Authorization Tests
# -------------------------------------------------------------------

def test_personalization_unauthenticated_requests():
    assert client.get("/api/v1/personalization").status_code == 401
    assert client.put("/api/v1/personalization/preferences", json={}).status_code == 401
    assert client.post("/api/v1/personalization/reset").status_code == 401
    assert client.delete("/api/v1/personalization/behavior/1").status_code == 401
    assert client.get("/api/v1/personalization/export").status_code == 401


def test_personalization_behavior_isolation_ownership():
    headers1, user1_id = _get_auth_headers("p_user1@example.com")
    headers2, user2_id = _get_auth_headers("p_user2@example.com")

    # Get overview for user 1 to seed behaviors
    resp1 = client.get("/api/v1/personalization", headers=headers1)
    b_id = resp1.json()["behaviors"][0]["id"]

    # User 2 tries to delete User 1's behavior -> 404 / 403 authorization guard
    del_resp = client.delete(f"/api/v1/personalization/behavior/{b_id}", headers=headers2)
    assert del_resp.status_code == 404


# -------------------------------------------------------------------
# 2. Preference Updates, Deletion, Reset, Export
# -------------------------------------------------------------------

def test_get_and_update_personalization_preferences():
    headers, user_id = _get_auth_headers("p_user3@example.com")

    # GET overview
    resp_get = client.get("/api/v1/personalization", headers=headers)
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["learning_enabled"] is True
    assert len(data_get["behaviors"]) == 4

    # PUT update settings
    update_payload = {
        "coaching_style": "motivational",
        "recommendation_frequency": "weekly",
        "response_detail": "detailed",
        "enable_memory": False
    }
    resp_put = client.put("/api/v1/personalization/preferences", headers=headers, json=update_payload)
    assert resp_put.status_code == 200
    data_put = resp_put.json()
    assert data_put["preferences"]["coaching_style"] == "motivational"
    assert data_put["preferences"]["recommendation_frequency"] == "weekly"
    assert data_put["preferences"]["enable_memory"] is False


def test_delete_single_learned_behavior():
    headers, user_id = _get_auth_headers("p_user4@example.com")

    overview = client.get("/api/v1/personalization", headers=headers).json()
    initial_count = len(overview["behaviors"])
    target_b_id = overview["behaviors"][0]["id"]

    # DELETE /behavior/{id}
    del_resp = client.delete(f"/api/v1/personalization/behavior/{target_b_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_id"] == target_b_id

    # Verify count decreased by 1
    new_overview = client.get("/api/v1/personalization", headers=headers).json()
    assert len(new_overview["behaviors"]) == initial_count - 1


def test_full_ai_reset_forget_everything():
    headers, user_id = _get_auth_headers("p_user5@example.com")

    client.get("/api/v1/personalization", headers=headers)

    # POST /reset
    reset_resp = client.post("/api/v1/personalization/reset", headers=headers)
    assert reset_resp.status_code == 200
    data_reset = reset_resp.json()

    assert data_reset["behaviors"] == []
    assert data_reset["preferences"]["coaching_style"] == "professional"
    assert data_reset["confidence"] == 0.50


def test_export_downloadable_ai_data_json():
    headers, user_id = _get_auth_headers("p_user6@example.com")

    client.get("/api/v1/personalization", headers=headers)

    # GET /export
    exp_resp = client.get("/api/v1/personalization/export", headers=headers)
    assert exp_resp.status_code == 200
    data_exp = exp_resp.json()

    assert data_exp["user_id"] == user_id
    assert "exported_at" in data_exp
    assert "preferences" in data_exp
    assert len(data_exp["behaviors"]) >= 1
    assert "statistics" in data_exp
