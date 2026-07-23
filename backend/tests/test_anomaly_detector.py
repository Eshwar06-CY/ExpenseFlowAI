"""
Unit & Integration Tests for AI Anomaly Detection Service - ExpenseFlowAI

Tests AIAnomalyDetectorService, FinanceEngine metrics extraction, LLM prompt formatting,
fallback execution, and API endpoints GET /anomalies and POST /anomalies/detect.
"""

import json
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
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.services.anomaly_detector import AIAnomalyDetectorService
from app.schemas.anomaly import AnomalySeverity, OverallRisk

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_anomaly_detector.db"
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
    user = db.query(User).filter(User.email == "anomaly_test@example.com").first()
    if not user:
        user = User(
            email="anomaly_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Anomaly Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Checking", type="checking", balance=100.0)
        db.add(account)
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service Tests (Mocked LLM)
# -------------------------------------------------------------------

def test_anomaly_service_no_anomalies():
    mock_provider = MagicMock()
    service = AIAnomalyDetectorService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="clean_user@example.com", password_hash="pw", full_name="Clean User")
    db.add(user)
    db.commit()

    # User with healthy balance and 0 expenses
    account = Account(user_id=user.id, name="Savings", type="savings", balance=15000.0)
    db.add(account)
    db.commit()

    report = service.detect_anomalies(db=db, user_id=user.id, period="30d")
    db.close()

    assert report["overall_risk"] == OverallRisk.LOW.value
    assert len(report["anomalies"]) == 0
    assert "No unusual spending anomalies" in report["summary"]


def test_anomaly_service_critical_reserve_anomaly():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = json.dumps({
        "anomalies": [{
            "severity": "CRITICAL",
            "category": "Emergency Reserve",
            "message": "Emergency fund is severely depleted.",
            "possible_reason": "Low liquid account balances relative to monthly expenses.",
            "recommendation": "Pause non-essential outflows immediately.",
            "confidence": 0.98
        }],
        "overall_risk": "CRITICAL",
        "summary": "Critical emergency fund depletion detected."
    })

    service = AIAnomalyDetectorService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="crit_user@example.com", password_hash="pw", full_name="Crit User")
    db.add(user)
    db.commit()

    account = Account(user_id=user.id, name="Checking", type="checking", balance=10.0)
    db.add(account)
    db.commit()

    from datetime import datetime, timedelta
    tx = Transaction(user_id=user.id, account_id=account.id, type="expense", amount=1000.0, date=datetime.utcnow() - timedelta(days=5))
    db.add(tx)
    db.commit()

    report = service.detect_anomalies(db=db, user_id=user.id, period="30d")
    db.close()

    assert report["overall_risk"] == OverallRisk.CRITICAL.value
    assert len(report["anomalies"]) >= 1
    assert report["anomalies"][0]["severity"] == AnomalySeverity.CRITICAL.value


def test_anomaly_service_budget_overspend_fallback():
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("LLM Offline")

    service = AIAnomalyDetectorService(provider=mock_provider)
    db = TestingSessionLocal()

    user = User(email="budget_user@example.com", password_hash="pw", full_name="Budget User")
    db.add(user)
    db.commit()

    cat = Category(user_id=user.id, name="Dining", type="expense", color="#FF0000")
    db.add(cat)
    db.commit()

    budget = Budget(user_id=user.id, category_id=cat.id, amount=100.0, spent=200.0, month="2026-07")
    db.add(budget)
    db.commit()

    report = service.detect_anomalies(db=db, user_id=user.id, period="30d")
    db.close()

    assert "anomalies" in report
    assert len(report["anomalies"]) >= 1
    assert report["anomalies"][0]["category"] in ["Dining", "Emergency Reserve"]


# -------------------------------------------------------------------
# 2. Router Endpoint Tests
# -------------------------------------------------------------------

def test_get_anomalies_unauthenticated():
    response = client.get("/api/v1/ai/anomalies")
    assert response.status_code == 401


@patch("app.services.anomaly_detector.AIAnomalyDetectorService.detect_anomalies")
def test_get_anomalies_authenticated_success(mock_detect):
    mock_detect.return_value = {
        "anomalies": [{
            "severity": "HIGH",
            "category": "Food & Dining",
            "message": "Food spending increased 55% compared to 30d baseline.",
            "possible_reason": "Frequent dining out.",
            "recommendation": "Reduce restaurant visits by two per week.",
            "confidence": 0.93
        }],
        "overall_risk": "MEDIUM",
        "summary": "1 high-priority spending spike detected."
    }

    headers = _get_auth_headers()
    response = client.get("/api/v1/ai/anomalies?period=30d", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "MEDIUM"
    assert len(data["anomalies"]) == 1
    assert data["anomalies"][0]["severity"] == "HIGH"


@patch("app.services.anomaly_detector.AIAnomalyDetectorService.detect_anomalies")
def test_post_detect_anomalies_success(mock_detect):
    mock_detect.return_value = {
        "anomalies": [],
        "overall_risk": "LOW",
        "summary": "No anomalies detected."
    }

    headers = _get_auth_headers()
    response = client.post("/api/v1/ai/anomalies/detect", headers=headers, json={"period": "30d"})

    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "LOW"
    assert data["summary"] == "No anomalies detected."
