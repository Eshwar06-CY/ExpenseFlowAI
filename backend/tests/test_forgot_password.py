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
from app.core.security import get_password_hash
from app.core.config import settings

DATABASE_URL = "sqlite:///./test_forgot_password.db"
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


def _create_user(email: str = "forgot_test@example.com") -> User:
    db = TestingSessionLocal()
    try:
        user = User(
            email=email,
            full_name="Forgot Tester",
            password_hash=get_password_hash("Password123!"),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_forgot_password_valid_email():
    user = _create_user("valid_user@example.com")

    with patch("app.routers.auth.send_password_reset_email") as mock_send_email:
        response = client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "If an account with that email exists, a password reset link has been sent."

    # Email dispatch called with raw token link
    mock_send_email.assert_called_once()
    call_kwargs = mock_send_email.call_args.kwargs
    raw_token = call_kwargs["reset_token"]
    assert len(raw_token) >= 32

    # Verify SHA-256 hash stored in DB, never raw token
    db = TestingSessionLocal()
    try:
        token_record = db.query(PasswordResetToken).filter_by(user_id=user.id).one()
        expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        
        assert token_record.token == expected_hash
        assert token_record.is_used is False
        assert token_record.used_at is None
        # Token expires based on settings config
        expiry_diff = token_record.expires_at.replace(tzinfo=None) - datetime.now(timezone.utc).replace(tzinfo=None)
        assert 25 <= expiry_diff.total_seconds() / 60 <= (settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES + 5)
    finally:
        db.close()


def test_forgot_password_non_existing_email():
    with patch("app.routers.auth.send_password_reset_email") as mock_send_email:
        response = client.post("/api/v1/auth/forgot-password", json={"email": "non_existent_address_999@example.com"})

    assert response.status_code == 200
    res_data = response.json()
    # Always return exact same generic message (no enumeration)
    assert res_data["success"] is True
    assert res_data["message"] == "If an account with that email exists, a password reset link has been sent."
    
    # No email sent and no token created
    mock_send_email.assert_not_called()
    db = TestingSessionLocal()
    try:
        assert db.query(PasswordResetToken).count() == 0
    finally:
        db.close()


def test_forgot_password_multiple_requests_invalidates_previous_tokens():
    user = _create_user("multi_request@example.com")

    # Request 1
    with patch("app.routers.auth.send_password_reset_email"):
        res1 = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert res1.status_code == 200

    db = TestingSessionLocal()
    try:
        first_token = db.query(PasswordResetToken).filter_by(user_id=user.id).one()
        first_token_hash = first_token.token
        assert first_token.is_used is False
    finally:
        db.close()

    # Request 2
    with patch("app.routers.auth.send_password_reset_email"):
        res2 = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert res2.status_code == 200

    db = TestingSessionLocal()
    try:
        tokens = db.query(PasswordResetToken).filter_by(user_id=user.id).order_by(PasswordResetToken.id.asc()).all()
        assert len(tokens) == 2
        # First token must be invalidated (is_used=True, used_at set)
        assert tokens[0].token == first_token_hash
        assert tokens[0].is_used is True
        assert tokens[0].used_at is not None

        # Second token is active
        assert tokens[1].is_used is False
        assert tokens[1].used_at is None
    finally:
        db.close()


def test_secure_logging_does_not_leak_raw_tokens(caplog):
    user = _create_user("secure_log@example.com")
    with patch("app.routers.auth.send_password_reset_email") as mock_send_email:
        with caplog.at_level(logging.INFO):
            response = client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    assert response.status_code == 200
    raw_token = mock_send_email.call_args.kwargs["reset_token"]

    # Verify raw token is NOT in any log record
    for record in caplog.records:
        assert raw_token not in record.getMessage()


def test_forgot_password_rate_limiting_configuration():
    from app.middleware.rate_limiter import RATE_LIMITS
    assert "/api/v1/auth/forgot-password" in RATE_LIMITS
    limit, window = RATE_LIMITS["/api/v1/auth/forgot-password"]
    assert limit == 3
    assert window == 60
