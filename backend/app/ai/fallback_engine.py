"""
Fallback Engine Service - ExpenseFlowAI Hybrid AI Architecture

Zero-LLM Fallback Engine that converts outputs from FinanceEngine and InsightRuleEngine
into readable, formatted text and structured JSON objects without invoking any external LLM.

Satisfies the LLMProvider interface so it can be used seamlessly as a fallback provider.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator

from app.ai.provider import LLMProvider
from app.ai.insight_rules import InsightRuleEngine, FinancialInsight
from app.ai.templates import TemplateEngine

logger = logging.getLogger(__name__)


class FallbackEngine(LLMProvider):
    def __init__(self):
        self.provider_name = "fallback_engine"
        self.model = "deterministic_rules"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generates deterministic text response based on rules & templates.
        """
        logger.info("[FALLBACK ENGINE ACTIVATED] Executing Rule Engine & Template Formatter without LLM.")
        
        summary_data = summary or {}
        insights = InsightRuleEngine.evaluate_rules(summary_data)
        
        user_msg = None
        if "USER QUESTION:" in prompt:
            user_msg = prompt.split("USER QUESTION:")[-1].split("ADVISOR RESPONSE:")[0].strip()
        elif "User Prompt Context:" in prompt:
            user_msg = prompt.split("User Prompt Context:")[-1].strip()

        return TemplateEngine.render_text_report(insights, summary_data, user_message=user_msg)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streams token chunks asynchronously from rendered template report to preserve SSE streaming API contract.
        """
        logger.info("[FALLBACK ENGINE ACTIVATED STREAM] Streaming token chunks from Fallback Engine.")
        
        full_text = self.generate(prompt=prompt, system_prompt=system_prompt, messages=messages, summary=summary, **kwargs)
        chunks = TemplateEngine.render_stream_chunks(full_text, words_per_chunk=4)

        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.02)  # Simulate real-time streaming velocity

    def generate_coaching_report(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates structured JSON coaching report matching AIFinancialCoachService schema.
        """
        logger.info("[FALLBACK ENGINE COACH] Generating structured coaching report deterministically.")
        insights = InsightRuleEngine.evaluate_rules(summary)
        return TemplateEngine.render_structured_coach(insights, summary)

    def health_check(self) -> Dict[str, Any]:
        """
        Fallback Engine is 100% deterministic local logic, always healthy.
        """
        return {
            "provider": self.provider_name,
            "model": self.model,
            "status": "healthy",
            "details": {"type": "Deterministic Rule Engine", "available": True}
        }
