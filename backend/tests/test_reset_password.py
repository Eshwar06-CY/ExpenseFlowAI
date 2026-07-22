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
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.core.security import get_password_hash, verify_password

DATABASE_URL = "sqlite:///./test_reset_password.db"
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


def _create_user(email: str = "reset_user@example.com") -> User:
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


def test_valid_password_reset_flow():
    user = _create_user("valid_reset@example.com")
    raw_token = "valid-raw-reset-token-xyz-123456789"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        token_obj = PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            is_used=False
        )
        db.add(token_obj)
        db.commit()
    finally:
        db.close()

    with patch("app.routers.auth.send_password_changed_email") as mock_changed_email:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
        )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    # Password changed confirmation email dispatched
    mock_changed_email.assert_called_once()
    assert mock_changed_email.call_args.kwargs["to_email"] == user.email

    # Verify user password updated and token marked used
    db = TestingSessionLocal()
    try:
        refreshed_user = db.get(User, user.id)
        refreshed_token = db.query(PasswordResetToken).filter_by(token=hashed_token).one()
        assert verify_password("NewSecurePassword123!", refreshed_user.password_hash)
        assert refreshed_token.is_used is True
        assert refreshed_token.used_at is not None
    finally:
        db.close()


def test_invalid_reset_token_rejected():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "completely-bogus-non-existent-token",
            "password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token."


def test_expired_reset_token_rejected():
    user = _create_user("expired_user@example.com")
    raw_token = "expired-token-12345"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            is_used=False
        ))
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_token,
            "password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_token_reuse_rejected():
    user = _create_user("reuse_user@example.com")
    raw_token = "reused-token-999"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            is_used=True,
            used_at=datetime.now(timezone.utc) - timedelta(minutes=2)
        ))
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_token,
            "password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token."


def test_weak_password_rejected():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "valid-token",
            "password": "weak",
            "confirm_password": "weak"
        }
    )
    assert response.status_code == 422


def test_mismatched_passwords_rejected():
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "valid-token",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!"
        }
    )
    assert response.status_code == 422


def test_reset_password_invalidates_all_other_user_tokens():
    user = _create_user("multi_tokens@example.com")
    raw_token_active = "active-token-1"
    hashed_active = hashlib.sha256(raw_token_active.encode("utf-8")).hexdigest()
    hashed_other = hashlib.sha256(b"other-token-2").hexdigest()

    db = TestingSessionLocal()
    try:
        db.add(PasswordResetToken(
            user_id=user.id,
            token=hashed_active,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            is_used=False
        ))
        db.add(PasswordResetToken(
            user_id=user.id,
            token=hashed_other,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            is_used=False
        ))
        db.commit()
    finally:
        db.close()

    with patch("app.routers.auth.send_password_changed_email"):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token_active,
                "password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
        )
    assert response.status_code == 200

    db = TestingSessionLocal()
    try:
        all_tokens = db.query(PasswordResetToken).filter_by(user_id=user.id).all()
        assert len(all_tokens) == 2
        for t in all_tokens:
            assert t.is_used is True
            assert t.used_at is not None
    finally:
        db.close()


def test_audit_logging_does_not_contain_passwords_or_raw_tokens(caplog):
    user = _create_user("audit_logging@example.com")
    raw_token = "audit-log-raw-token-123456"
    hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    new_password = "SuperSecretPassword123!"

    db = TestingSessionLocal()
    try:
        db.add(PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            is_used=False
        ))
        db.commit()
    finally:
        db.close()

    with patch("app.routers.auth.send_password_changed_email"):
        with caplog.at_level(logging.INFO):
            res = client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": raw_token,
                    "password": new_password,
                    "confirm_password": new_password
                }
            )

    assert res.status_code == 200
    for record in caplog.records:
        log_msg = record.getMessage()
        assert new_password not in log_msg
        assert raw_token not in log_msg
