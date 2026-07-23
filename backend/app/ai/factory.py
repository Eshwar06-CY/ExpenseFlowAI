"""
AI Provider Factory - ExpenseFlowAI Hybrid AI Architecture

Dynamically instantiates and returns the configured HybridLLMProvider,
combining Primary LLM (Google Gemini 3.6 Flash) with deterministic FallbackEngine.
Ensures resilient provider instantiation across all AI features.
"""

import logging
from typing import Optional

from app.core.config import settings
from app.ai.provider import LLMProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.fallback_engine import FallbackEngine
from app.ai.hybrid_provider import HybridLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_name: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function returning a resilient HybridLLMProvider instance
    wrapping GeminiProvider as primary and FallbackEngine as secondary.
    """
    primary = GeminiProvider(**kwargs)
    fallback = FallbackEngine()
    return HybridLLMProvider(primary_provider=primary, fallback_provider=fallback)
