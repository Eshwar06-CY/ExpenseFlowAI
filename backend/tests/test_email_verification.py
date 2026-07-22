import hashlib
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User
from app.models.email_verification import EmailVerificationToken
from app.core.security import get_password_hash

DATABASE_URL = "sqlite:///./test_email_verification.db"
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


def _create_user(email: str = "unverified_user@example.com", is_verified: bool = False) -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            email=email,
            full_name="Verification Tester",
            password_hash=get_password_hash("Password123!"),
            is_active=True,
            is_verified=is_verified,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_successful_email_verification():
    user = _create_user("verify_me@example.com", is_verified=False)
    raw_token = "verification-raw-token-123456789"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(EmailVerificationToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_used=False
        ))
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/auth/verify-email?token={raw_token}")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "Email verified successfully."

    # Assert database updates
    db = TestingSessionLocal()
    try:
        refreshed_user = db.get(User, user.id)
        token_record = db.query(EmailVerificationToken).filter_by(token=hashed_token).one()

        assert refreshed_user.is_verified is True
        assert refreshed_user.email_verified_at is not None
        assert token_record.is_used is True
        assert token_record.used_at is not None
    finally:
        db.close()


def test_invalid_verification_token():
    response = client.get("/api/v1/auth/verify-email?token=bogus-invalid-token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token."


def test_expired_verification_token():
    user = _create_user("expired_verify@example.com", is_verified=False)
    raw_token = "expired-token-123"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(EmailVerificationToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_used=False
        ))
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/auth/verify-email?token={raw_token}")
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_reused_verification_token():
    user = _create_user("reused_verify@example.com", is_verified=False)
    raw_token = "reused-token-456"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(EmailVerificationToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_used=True,
            used_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        ))
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/auth/verify-email?token={raw_token}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token."


def test_resend_verification_creates_new_token_and_dispatches_email():
    user = _create_user("resend_user@example.com", is_verified=False)

    with patch("app.routers.auth.send_verification_email") as mock_send_email:
        response = client.post("/api/v1/auth/resend-verification", json={"email": user.email})

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    mock_send_email.assert_called_once()
    raw_token = mock_send_email.call_args.kwargs["verification_token"]
    assert len(raw_token) >= 32

    # Database check
    db = TestingSessionLocal()
    try:
        token_record = db.query(EmailVerificationToken).filter_by(user_id=user.id).one()
        expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        assert token_record.token == expected_hash
        assert token_record.is_used is False
    finally:
        db.close()


def test_resend_verification_already_verified_account():
    user = _create_user("already_verified@example.com", is_verified=True)

    with patch("app.routers.auth.send_verification_email") as mock_send_email:
        response = client.post("/api/v1/auth/resend-verification", json={"email": user.email})

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    # Email not sent for already verified account
    mock_send_email.assert_not_called()


def test_login_returns_is_email_verified_flag():
    user = _create_user("login_verify_flag@example.com", is_verified=False)

    response = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "Password123!"
    })

    assert response.status_code == 200
    res_data = response.json()
    assert "access_token" in res_data
    assert res_data["is_email_verified"] is False
