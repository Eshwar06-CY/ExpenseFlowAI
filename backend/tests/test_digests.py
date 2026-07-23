"""
Unit & Integration Tests for AI Financial Digest & PDF Reporting System - ExpenseFlowAI
"""

import os
from datetime import datetime, timedelta
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
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.services.cache import cache_service

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_digests.db"
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


def _get_auth_headers(email="digest_user@example.com"):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash="fake_password_hash",
            full_name="Executive Digest User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(user_id=user.id, name="Corporate Account", type="checking", balance=250000.0)
        db.add(account)

        cat = Category(user_id=user.id, name="Travel", type="expense")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        now = datetime.now()
        tx_inc = Transaction(user_id=user.id, account_id=account.id, type="income", amount=120000.0, date=now - timedelta(days=2))
        tx_exp = Transaction(user_id=user.id, account_id=account.id, category_id=cat.id, type="expense", amount=35000.0, date=now - timedelta(days=1))
        db.add_all([tx_inc, tx_exp])

        budget = Budget(user_id=user.id, category_id=cat.id, amount=40000.0, spent=35000.0, month="2026-07")
        goal = Goal(user_id=user.id, name="Investment Target", target_amount=300000.0, current_amount=180000.0)
        bill = Bill(user_id=user.id, name="Software Subscription", amount=2500.0, due_date=now + timedelta(days=3), is_paid=False)
        db.add_all([budget, goal, bill])
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}, user.id


def test_digests_unauthenticated():
    response = client.get("/api/v1/digests")
    assert response.status_code == 401


def test_generate_digest_and_pdf():
    headers, user_id = _get_auth_headers()
    response = client.post(
        "/api/v1/digests/generate",
        json={"digest_type": "monthly"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "id" in data
    assert data["digest_type"] == "monthly"
    assert data["health_score"] > 0
    assert data["has_pdf"] is True
    assert "content" in data


def test_get_latest_digest():
    headers, user_id = _get_auth_headers("latest_digest@example.com")
    gen_res = client.post("/api/v1/digests/generate", json={"digest_type": "weekly"}, headers=headers)
    assert gen_res.status_code == 200

    latest_res = client.get("/api/v1/digests/latest", headers=headers)
    assert latest_res.status_code == 200
    assert latest_res.json()["digest_type"] == "weekly"


def test_download_digest_pdf():
    headers, user_id = _get_auth_headers("pdf_download@example.com")
    gen_res = client.post("/api/v1/digests/generate", json={"digest_type": "monthly"}, headers=headers)
    digest_id = gen_res.json()["id"]

    dl_res = client.get(f"/api/v1/digests/{digest_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) > 1000  # Non-empty PDF bytes


def test_list_digests():
    headers, user_id = _get_auth_headers("list_digest@example.com")
    client.post("/api/v1/digests/generate", json={"digest_type": "monthly"}, headers=headers)

    list_res = client.get("/api/v1/digests", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total_count"] >= 1
    assert len(data["items"]) >= 1
