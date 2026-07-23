"""
Unit & Integration Tests for Smart Notification Center - ExpenseFlowAI
"""

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
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.notification import Notification, NotificationPreference
from app.services.cache import cache_service

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notifications.db"
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


def _get_auth_headers(email="notify_user@example.com"):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash="fake_password_hash",
            full_name="Notification User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        cat = Category(user_id=user.id, name="Dining Out", type="expense")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        # Create threshold breach budget & upcoming bill
        budget = Budget(user_id=user.id, category_id=cat.id, amount=10000.0, spent=10500.0, month="2026-07")
        goal = Goal(user_id=user.id, name="Emergency Fund", target_amount=50000.0, current_amount=50000.0)
        now = datetime.now()
        bill = Bill(user_id=user.id, name="Internet Bill", amount=1200.0, due_date=now + timedelta(hours=2), is_paid=False)
        db.add_all([budget, goal, bill])
        db.commit()

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}, user.id


def test_notifications_unauthenticated():
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401


def test_smart_notification_generation_and_list():
    headers, user_id = _get_auth_headers()
    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "unread_count" in data
    assert data["total_count"] >= 2
    assert data["unread_count"] >= 2

    # Check for budget exceeded and goal completed alerts
    titles = [item["title"] for item in data["items"]]
    assert any("Budget Exceeded" in t for t in titles)
    assert any("Goal Completed" in t for t in titles)


def test_mark_notification_as_read():
    headers, user_id = _get_auth_headers("read_test@example.com")
    list_res = client.get("/api/v1/notifications", headers=headers)
    items = list_res.json()["items"]
    assert len(items) > 0

    notif_id = items[0]["id"]
    read_res = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True


def test_mark_all_notifications_as_read():
    headers, user_id = _get_auth_headers("read_all_test@example.com")
    # Fetch list to trigger initial notification generation
    initial_res = client.get("/api/v1/notifications", headers=headers)
    assert initial_res.json()["unread_count"] > 0

    read_all_res = client.patch("/api/v1/notifications/read-all", headers=headers)
    assert read_all_res.status_code == 200

    list_res = client.get("/api/v1/notifications", headers=headers)
    assert list_res.json()["unread_count"] == 0


def test_delete_notification():
    headers, user_id = _get_auth_headers("delete_test@example.com")
    list_res = client.get("/api/v1/notifications", headers=headers)
    items = list_res.json()["items"]
    assert len(items) > 0

    notif_id = items[0]["id"]
    del_res = client.delete(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert del_res.status_code == 200

    list_after = client.get("/api/v1/notifications", headers=headers)
    assert not any(item["id"] == notif_id for item in list_after.json()["items"])


def test_notification_preferences_get_and_update():
    headers, user_id = _get_auth_headers("pref_test@example.com")
    get_res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert prefs["enable_budget_alerts"] is True

    update_res = client.put(
        "/api/v1/notifications/preferences",
        json={"enable_budget_alerts": False, "digest_frequency": "daily"},
        headers=headers
    )
    assert update_res.status_code == 200
    updated_prefs = update_res.json()["preferences"]
    assert updated_prefs["enable_budget_alerts"] is False
    assert updated_prefs["digest_frequency"] == "daily"
