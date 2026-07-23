"""
Response Validator Module - ExpenseFlowAI Multi-Stage Reasoning Pipeline

Validates generated AI responses before returning to client:
1. Ensures greetings and small talk never contain unrequested raw financial metric blocks.
2. Validates that clarification questions are present when required inputs are missing.
3. Performs response sanitization and quality checks.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from app.ai.intent_classifier import IntentType
from app.ai.decision_engine import DecisionResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_text: str
    warnings: List[str]


class ResponseValidator:
    @classmethod
    def validate_and_sanitize(
        cls,
        response_text: str,
        decision_result: DecisionResult,
        user_message: str
    ) -> ValidationResult:
        """
        Validates generated text against intent rules and decision result.
        """
        text = (response_text or "").strip()
        warnings = []

        if not text:
            logger.warning("[ResponseValidator] Empty response generated.")
            return ValidationResult(
                is_valid=False,
                sanitized_text="I'm sorry, I couldn't process that. Please try again.",
                warnings=["Empty response"]
            )

        # Rule 1: Non-financial intents (Greetings, Small Talk, Jokes) must NOT contain heavy report headers
        if not decision_result.use_finance_engine:
            for forbidden in ["Composite Score:", "VERIFIED FINANCIAL METRICS", "Executive Financial Assessment"]:
                if forbidden in text:
                    logger.warning("[ResponseValidator] Strip forbidden metric block from non-financial intent: '%s'", forbidden)
                    warnings.append(f"Forbidden block removed: {forbidden}")
                    # Strip the raw metric block if hallucinated by LLM
                    lines = text.split("\n")
                    clean_lines = [l for l in lines if not any(f in l for f in ["Composite Score:", "VERIFIED FINANCIAL METRICS", "Executive Financial Assessment"])]
                    text = "\n".join(clean_lines).strip()

        # Rule 2: Clarification decision must contain questions
        if decision_result.should_clarify and "?" not in text:
            warnings.append("Clarification response missing question marks")

        logger.info("[ResponseValidator] Validation complete (Valid: True, Warnings: %s)", warnings)
        return ValidationResult(
            is_valid=True,
            sanitized_text=text,
            warnings=warnings
        )
