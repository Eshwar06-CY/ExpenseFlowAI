"""End-to-end tests for password reset token issuance and consumption."""

from datetime import datetime, timedelta, timezone
import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.core.security import get_password_hash, verify_password


DATABASE_URL = "sqlite:///./test_password_reset.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database():
    """Use this module's database despite other test modules sharing ``app``."""
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


def _create_user(email: str = "reset@example.com") -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            email=email,
            full_name="Reset Tester",
            password_hash=get_password_hash("OriginalPass123!"),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_forgot_password_generates_single_use_token():
    user = _create_user()
    with patch("app.routers.auth.send_password_reset_email") as send_email:
        response = client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    assert response.status_code == 200
    assert response.json()["success"] is True
    send_email.assert_called_once()

    db = TestingSessionLocal()
    try:
        token = db.query(PasswordResetToken).filter_by(user_id=user.id).one()
        assert len(token.token) >= 40
        assert token.is_used is False
        assert token.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    finally:
        db.close()


def test_reset_password_updates_password_and_consumes_token():
    user = _create_user("complete@example.com")
    db = TestingSessionLocal()
    try:
        reset_token = PasswordResetToken(
            user_id=user.id,
            token="valid-reset-token",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(reset_token)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "valid-reset-token", "new_password": "UpdatedPass123!"},
    )
    assert response.status_code == 200

    db = TestingSessionLocal()
    try:
        refreshed_user = db.get(User, user.id)
        refreshed_token = db.query(PasswordResetToken).filter_by(token="valid-reset-token").one()
        assert verify_password("UpdatedPass123!", refreshed_user.password_hash)
        assert refreshed_token.is_used is True
    finally:
        db.close()


def test_expired_or_invalid_token_is_rejected():
    user = _create_user("expired@example.com")
    db = TestingSessionLocal()
    try:
        db.add(PasswordResetToken(
            user_id=user.id,
            token="expired-reset-token",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        ))
        db.commit()
    finally:
        db.close()

    expired = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "expired-reset-token", "new_password": "UpdatedPass123!"},
    )
    invalid = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "UpdatedPass123!"},
    )

    assert expired.status_code == 400
    assert invalid.status_code == 400

    db = TestingSessionLocal()
    try:
        expired_token = db.query(PasswordResetToken).filter_by(token="expired-reset-token").one()
        assert expired_token.is_used is True
    finally:
        db.close()
