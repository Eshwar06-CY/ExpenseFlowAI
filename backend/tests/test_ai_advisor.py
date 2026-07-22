"""
Unit & Integration Tests for AI Financial Advisor Module - ExpenseFlowAI

Tests PromptBuilder, OllamaProvider (mocked), AIAdvisorService (mocked),
/ai/health, and /ai/chat endpoints without calling real LLMs.
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
from app.ai.prompt_builder import PromptBuilder
from app.ai.ollama_provider import OllamaProvider
from app.ai.advisor import AIAdvisorService

# Isolated test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_advisor.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _get_auth_headers():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "ai_test@example.com").first()
    if not user:
        user = User(
            email="ai_test@example.com",
            password_hash="fake_hashed_password",
            full_name="AI Test User",
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
# 1. PromptBuilder Unit Tests
# -------------------------------------------------------------------

def test_prompt_builder_format():
    summary = {
        "total_balance": 15000.50,
        "period": "30d",
        "period_income": 5000.0,
        "period_expense": 2000.0,
        "period_savings": 3000.0,
        "period_savings_rate": 60.0,
        "health_score": 85,
        "health_status": "Healthy",
        "category_spending": [
            {"category": "Dining Out", "amount": 450.0, "percentage": 22.5},
            {"category": "Groceries", "amount": 350.0, "percentage": 17.5}
        ],
        "health_metrics": {
            "reserve_months": 7.5,
            "budget_adherence_pct": 90.0,
            "bill_reliability_pct": 100.0
        }
    }

    prompt = PromptBuilder.build_prompt(summary, user_message="How can I save more?")

    assert "Total Available Balance: $15,000.50" in prompt
    assert "Savings Rate: 60.0%" in prompt
    assert "Financial Health Score: 85/100 (Healthy)" in prompt
    assert "Dining Out: $450.00" in prompt
    assert "USER QUESTION:\nHow can I save more?" in prompt


# -------------------------------------------------------------------
# 2. OllamaProvider Unit Tests (Mocked HTTP)
# -------------------------------------------------------------------

@patch("httpx.Client.post")
def test_ollama_provider_generate_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "You should automate savings."}
    mock_post.return_value = mock_response

    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b")
    res = provider.generate("Test Prompt")

    assert res == "You should automate savings."
    mock_post.assert_called_once()


@patch("httpx.Client.get")
def test_ollama_provider_health_check(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "qwen3:8b"}, {"name": "llama3:latest"}]
    }
    mock_get.return_value = mock_response

    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b")
    health = provider.health_check()

    assert health["status"] == "healthy"
    assert health["provider"] == "ollama"
    assert health["model"] == "qwen3:8b"


# -------------------------------------------------------------------
# 3. AIAdvisorService Unit Tests
# -------------------------------------------------------------------

def test_ai_advisor_service_ask():
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Try cutting dining expenses by 10%."
    mock_provider.provider_name = "ollama"
    mock_provider.model = "qwen3:8b"

    service = AIAdvisorService(provider=mock_provider)
    db = TestingSessionLocal()

    # Seed mock user
    user = User(email="service_user@example.com", password_hash="pw", full_name="User")
    db.add(user)
    db.commit()

    result = service.ask(db=db, user_id=user.id, message="Any recommendations?")
    db.close()

    assert result["response"] == "Try cutting dining expenses by 10%."
    assert result["provider"] == "ollama"
    mock_provider.generate.assert_called_once()


# -------------------------------------------------------------------
# 4. API Router Endpoints Tests
# -------------------------------------------------------------------

def test_get_ai_health_endpoint():
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert "status" in data


def test_post_ai_chat_unauthenticated():
    response = client.post("/api/v1/ai/chat", json={"message": "Hello?"})
    assert response.status_code == 401


@patch("app.ai.ollama_provider.OllamaProvider.generate")
def test_post_ai_chat_authenticated_success(mock_generate):
    mock_generate.return_value = "Based on your 60% savings rate, your finances look strong!"
    headers = _get_auth_headers()

    response = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "How are my finances looking?", "period": "30d"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Based on your 60% savings rate, your finances look strong!"
    assert data["provider"] == "ollama"
    assert data["model"] == "qwen3:8b"
