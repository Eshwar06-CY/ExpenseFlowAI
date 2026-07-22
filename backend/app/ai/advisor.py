"""
AI Advisor Service - ExpenseFlowAI

Orchestrates financial data retrieval from FinanceEngine, context building
via PromptBuilder, and text generation via an abstract LLMProvider.
Contains NO SQL queries or direct database table manipulations.
"""

from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session

from app.services.finance_engine import FinanceEngine
from app.ai.provider import LLMProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.prompt_builder import PromptBuilder


class AIAdvisorService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or OllamaProvider()

    def ask(
        self,
        db: Session,
        user_id: int,
        message: str,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Executes full advisory pipeline:
        1. Fetch verified financial metrics from FinanceEngine
        2. Build prompt context
        3. Invoke provider generation
        4. Return response metadata
        """
        # Fetch verified financial summary from FinanceEngine
        financial_summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)

        # Build prompt & system prompt
        prompt = PromptBuilder.build_prompt(financial_summary, user_message=message)
        system_prompt = PromptBuilder.get_system_prompt()

        # Generate response via provider
        response_text = self.provider.generate(prompt=prompt, system_prompt=system_prompt)

        return {
            "response": response_text,
            "provider": getattr(self.provider, "provider_name", "ollama"),
            "model": getattr(self.provider, "model", "qwen3:8b"),
        }

    async def ask_stream(
        self,
        db: Session,
        user_id: int,
        message: str,
        period: str = "30d"
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams token chunks for real-time response generation.
        """
        financial_summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        prompt = PromptBuilder.build_prompt(financial_summary, user_message=message)
        system_prompt = PromptBuilder.get_system_prompt()

        async for chunk in self.provider.generate_stream(prompt=prompt, system_prompt=system_prompt):
            yield chunk

    def health_check(self) -> Dict[str, Any]:
        """
        Returns health status of the configured LLM provider.
        """
        return self.provider.health_check()
