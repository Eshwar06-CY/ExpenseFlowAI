"""
AI Advisor Service - ExpenseFlowAI Intent-Aware Architecture

Orchestrates financial data retrieval from FinanceEngine ONLY when required,
context building via PromptBuilder, and text generation via an abstract LLMProvider / HybridLLMProvider.
Contains NO SQL queries or direct database table manipulations.
"""

from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.finance_engine import FinanceEngine
from app.services.memory_service import AIMemoryService
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.ai.prompt_builder import PromptBuilder
from app.ai.intent_classifier import IntentClassifier


class AIAdvisorService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def ask(
        self,
        db: Session,
        user_id: int,
        message: str,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Executes full advisory pipeline:
        1. Classify user intent
        2. Fetch verified financial metrics from FinanceEngine ONLY if intent requires data
        3. Fetch relevant persistent user memories from AIMemoryService
        4. Build intent-driven prompt & system prompt
        5. Invoke provider generation (with automatic rule-engine fallback)
        """
        intent, requires_data = IntentClassifier.classify(user_message=message)

        financial_summary = None
        if requires_data:
            financial_summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)

        # Retrieve top relevant memories
        memories = []
        try:
            memories = AIMemoryService.get_relevant_memories(db, user_id=user_id, query_text=message, limit=10)
        except Exception:
            pass

        # Build prompt & system prompt based on intent
        prompt = PromptBuilder.build_prompt(
            financial_summary=financial_summary,
            user_message=message,
            memories=memories
        )
        system_prompt = PromptBuilder.get_system_prompt_for_message(message)

        # Generate response via hybrid provider
        response_text = self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            summary=financial_summary
        )

        return {
            "response": response_text,
            "provider": getattr(self.provider, "provider_name", "gemini"),
            "model": getattr(self.provider, "model", settings.GEMINI_MODEL),
        }

    async def ask_stream(
        self,
        db: Session,
        user_id: int,
        message: str,
        period: str = "30d"
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams token chunks with intent classification context.
        """
        intent, requires_data = IntentClassifier.classify(user_message=message)

        financial_summary = None
        if requires_data:
            financial_summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)

        memories = []
        try:
            memories = AIMemoryService.get_relevant_memories(db, user_id=user_id, query_text=message, limit=10)
        except Exception:
            pass

        prompt = PromptBuilder.build_prompt(
            financial_summary=financial_summary,
            user_message=message,
            memories=memories
        )
        system_prompt = PromptBuilder.get_system_prompt_for_message(message)

        async for chunk in self.provider.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            summary=financial_summary
        ):
            yield chunk

    def health_check(self) -> Dict[str, Any]:
        """
        Returns health status of the configured LLM provider.
        """
        return self.provider.health_check()
