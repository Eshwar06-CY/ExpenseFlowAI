"""
Unit & Integration Tests for AI Persistent Memory Service - ExpenseFlowAI

Tests AIMemoryService CRUD operations, relevance ranking, limit=10 capping,
PromptBuilder integration, and privacy API endpoints (List, Create, Update, Delete, Export).
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
from app.models.memory import AIMemory
from app.services.memory_service import AIMemoryService
from app.ai.prompt_builder import PromptBuilder

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_memory_service.db"
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
    user = db.query(User).filter(User.email == "memory_test@example.com").first()
    if not user:
        user = User(
            email="memory_test@example.com",
            password_hash="fake_hashed_password",
            full_name="Memory Test User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# 1. Service & Ranking Tests
# -------------------------------------------------------------------

def test_memory_crud_and_upsert():
    db = TestingSessionLocal()
    user = User(email="mem_user1@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # Create memory
    mem1 = AIMemoryService.remember(
        db=db,
        user_id=user.id,
        category="financial_goal",
        key="macbook_goal",
        value="MacBook Pro M4",
        confidence=0.95
    )
    assert mem1.id is not None
    assert mem1.value == "MacBook Pro M4"

    # Upsert existing memory
    mem1_updated = AIMemoryService.remember(
        db=db,
        user_id=user.id,
        category="financial_goal",
        key="macbook_goal",
        value="MacBook Pro M4 32GB",
        confidence=0.99
    )
    assert mem1_updated.id == mem1.id
    assert mem1_updated.value == "MacBook Pro M4 32GB"

    # Get active memories
    active_mems = AIMemoryService.get_memories(db=db, user_id=user.id)
    assert len(active_mems) == 1

    # Delete memory
    deleted = AIMemoryService.delete_memory(db=db, user_id=user.id, memory_id=mem1.id)
    assert deleted is True

    # Export memories
    export_data = AIMemoryService.export_memories(db=db, user_id=user.id)
    assert export_data["total_memories"] == 0
    db.close()


def test_memory_relevance_ranking_limit_cap():
    db = TestingSessionLocal()
    user = User(email="rank_user@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    # Add 15 memory items to test limit <= 10 cap
    for i in range(15):
        AIMemoryService.remember(
            db=db,
            user_id=user.id,
            category="lifestyle_note" if i % 2 == 0 else "financial_goal",
            key=f"item_{i}",
            value=f"Memory detail number {i} MacBook",
            confidence=0.5 + (i * 0.03)
        )

    relevant = AIMemoryService.get_relevant_memories(db=db, user_id=user.id, query_text="MacBook", limit=10)
    assert len(relevant) == 10
    db.close()


def test_prompt_builder_memory_injection():
    summary = {
        "total_balance": 10000.0,
        "period": "30d",
        "period_income": 5000.0,
        "period_expense": 2000.0,
        "period_savings": 3000.0,
        "period_savings_rate": 60.0,
        "health_score": 85,
        "health_status": "Healthy"
    }

    mock_memories = [
        {"category": "financial_goal", "key": "macbook_goal", "value": "MacBook Pro M4"},
        {"category": "lifestyle_note", "key": "city", "value": "Bangalore"}
    ]

    prompt = PromptBuilder.build_prompt(
        financial_summary=summary,
        user_message="How am I doing on my goals?",
        memories=mock_memories
    )

    assert "PERSISTENT USER MEMORIES & PREFERENCES:" in prompt
    assert "macbook_goal: MacBook Pro M4" in prompt
    assert "city: Bangalore" in prompt


# -------------------------------------------------------------------
# 2. Router Privacy API Endpoint Tests
# -------------------------------------------------------------------

def test_memories_unauthenticated():
    response = client.get("/api/v1/ai/memories")
    assert response.status_code == 401


def test_create_and_list_memories_api():
    headers = _get_auth_headers()

    # Create memory via API
    create_resp = client.post(
        "/api/v1/ai/memories",
        headers=headers,
        json={
            "category": "lifestyle_note",
            "key": "city",
            "value": "Bangalore",
            "confidence": 0.95
        }
    )
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["key"] == "city"
    assert data["value"] == "Bangalore"
    memory_id = data["id"]

    # List memories via API
    list_resp = client.get("/api/v1/ai/memories", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) >= 1

    # Update memory via API
    update_resp = client.put(
        f"/api/v1/ai/memories/{memory_id}",
        headers=headers,
        json={"value": "Mumbai"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["value"] == "Mumbai"

    # Export memories via API
    export_resp = client.get("/api/v1/ai/memories/export", headers=headers)
    assert export_resp.status_code == 200
    assert export_resp.json()["total_memories"] >= 1

    # Delete memory via API
    delete_resp = client.delete(f"/api/v1/ai/memories/{memory_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Memory record successfully deleted."
