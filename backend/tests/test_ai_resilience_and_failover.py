"""
Specialized Resilience & Failover Automated Test Suite - ExpenseFlowAI

Tests:
1. GeminiProvider thread-safe client cache.
2. HybridLLMProvider automatic failover under quota limit, timeout, network outage, invalid key, and 404 errors.
3. ChatStreamService SSE token stream resilience under primary stream failures.
4. Non-calculation prompt constraints verification.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.ai.provider import LLMProvider
from app.ai.gemini_provider import GeminiProvider, _CLIENT_CACHE
from app.ai.fallback_engine import FallbackEngine
from app.ai.hybrid_provider import HybridLLMProvider
from app.ai.prompt_builder import PromptBuilder
from app.ai.insight_rules import InsightRuleEngine


@pytest.fixture
def sample_summary():
    return {
        "total_balance": 12000.0,
        "period": "30d",
        "period_income": 4000.0,
        "period_expense": 3200.0,
        "period_savings": 800.0,
        "period_savings_rate": 20.0,
        "health_score": 75,
        "health_status": "Healthy",
        "health_metrics": {
            "reserve_months": 3.75,
            "budget_adherence_pct": 90.0,
            "bill_reliability_pct": 100.0,
        },
        "category_spending": [
            {"category": "Rent", "amount": 1600.0, "percentage": 50.0},
            {"category": "Groceries", "amount": 600.0, "percentage": 18.75},
        ]
    }


# -------------------------------------------------------------------
# 1. Gemini Client Cache & Singleton Reuse
# -------------------------------------------------------------------

def test_gemini_client_caching():
    provider1 = GeminiProvider(api_key="test_dummy_key_1")
    provider2 = GeminiProvider(api_key="test_dummy_key_1")

    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance

        c1 = provider1._get_client()
        c2 = provider2._get_client()

        assert c1 is c2
        assert mock_client_cls.call_count == 1


# -------------------------------------------------------------------
# 2. HybridLLMProvider Automatic Failover Scenarios
# -------------------------------------------------------------------

def test_failover_quota_exceeded(sample_summary):
    mock_primary = MagicMock()
    mock_primary.generate.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED: Quota exceeded for metric")

    hybrid = HybridLLMProvider(primary_provider=mock_primary)
    response = hybrid.generate(prompt="How to cut expenses?", summary=sample_summary)

    assert len(response) > 50
    assert "Executive Financial Assessment" in response or "Financial Health Overview" in response
    mock_primary.generate.assert_called_once()


def test_failover_network_timeout(sample_summary):
    mock_primary = MagicMock()
    mock_primary.generate.side_effect = TimeoutError("Connection to Google API timed out after 60.0s")

    hybrid = HybridLLMProvider(primary_provider=mock_primary)
    response = hybrid.generate(prompt="Analyze savings", summary=sample_summary)

    assert "$12,000.00" in response
    mock_primary.generate.assert_called_once()


def test_failover_invalid_api_key(sample_summary):
    mock_primary = MagicMock()
    mock_primary.generate.side_effect = RuntimeError("400 API_KEY_INVALID: API key not valid.")

    hybrid = HybridLLMProvider(primary_provider=mock_primary)
    response = hybrid.generate(prompt="Analyze budget", summary=sample_summary)

    assert "Financial Observations" in response
    mock_primary.generate.assert_called_once()


def test_failover_model_404_not_found(sample_summary):
    mock_primary = MagicMock()
    mock_primary.generate.side_effect = RuntimeError("404 NOT_FOUND: Model gemini-2.5-flash is no longer available.")

    hybrid = HybridLLMProvider(primary_provider=mock_primary)
    response = hybrid.generate(prompt="Check runway", summary=sample_summary)

    assert "Liquid Balance" in response
    mock_primary.generate.assert_called_once()


# -------------------------------------------------------------------
# 3. Streaming Failover Resilience
# -------------------------------------------------------------------

def test_stream_failover_on_error_chunk(sample_summary):
    mock_primary = MagicMock()

    async def _failing_stream(prompt, system_prompt=None, summary=None, **kwargs):
        yield "Partial text... "
        yield "\n[Gemini API Error: 503 Service Unavailable]"

    mock_primary.generate_stream = _failing_stream

    hybrid = HybridLLMProvider(primary_provider=mock_primary)

    async def _collect():
        chunks = []
        async for chunk in hybrid.generate_stream(prompt="Stream test", summary=sample_summary):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_collect())
    full_text = "".join(chunks)

    assert len(chunks) > 0
    assert "Executive Financial Assessment" in full_text or "Liquid Balance" in full_text


# -------------------------------------------------------------------
# 4. Prompt Integrity & Non-Calculation Boundary
# -------------------------------------------------------------------

def test_prompt_builder_non_calculation_boundary(sample_summary):
    prompt = PromptBuilder.build_prompt(financial_summary=sample_summary, user_message="How can I optimize my monthly expenses?")
    
    assert "VERIFIED FINANCIAL METRICS" in prompt
    assert "VERIFIED RULE ENGINE INSIGHTS" in prompt
    assert "DO NOT recalculate or modify any financial numbers" in prompt
    assert "$12,000.00" in prompt


# -------------------------------------------------------------------
# 5. Configuration Integrity
# -------------------------------------------------------------------

def test_config_model_default():
    assert settings.GEMINI_MODEL is not None
    assert "gemini-2.5-flash" not in settings.GEMINI_MODEL
