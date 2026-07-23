"""
Decision Engine Module - ExpenseFlowAI Multi-Stage Pipeline

Evaluates IntentResult, ExtractedEntities, and TaskPlan to decide:
1. Whether FinanceEngine DB reads are required
2. Whether the assistant should ask clarification questions for missing data
3. Which prompt template should be selected for LLM consumption
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

from app.ai.intent_classifier import IntentType, IntentResult
from app.ai.entity_extractor import ExtractedEntities
from app.ai.task_planner import TaskPlan

logger = logging.getLogger(__name__)


@dataclass
class DecisionResult:
    use_finance_engine: bool
    should_clarify: bool
    template_key: str
    decision_reason: str


class DecisionEngine:
    @classmethod
    def evaluate(
        cls,
        intent_result: IntentResult,
        entities: ExtractedEntities,
        task_plan: TaskPlan
    ) -> DecisionResult:
        """
        Evaluates system state and outputs DecisionResult.
        """
        intent = intent_result.intent

        # 1. Missing information clarification decision
        if not task_plan.is_complete and task_plan.clarification_prompt:
            logger.info("[DecisionEngine] Decision: CLARIFY_MISSING_INFO for intent '%s'", intent.value)
            return DecisionResult(
                use_finance_engine=False,
                should_clarify=True,
                template_key="clarification",
                decision_reason=f"Missing required fields: {task_plan.missing_fields}"
            )

        # 2. Conversational intents (Greetings, Small Talk, Identity, Help, Jokes)
        if not intent_result.requires_financial_data:
            logger.info("[DecisionEngine] Decision: CONVERSATIONAL for intent '%s'", intent.value)
            return DecisionResult(
                use_finance_engine=False,
                should_clarify=False,
                template_key=intent.value,
                decision_reason="Conversational intent does not require financial DB metrics"
            )

        # 3. Financial Analysis / Advice / Goal Planning intents with complete data
        logger.info("[DecisionEngine] Decision: FINANCIAL_ANALYSIS for intent '%s'", intent.value)
        return DecisionResult(
            use_finance_engine=True,
            should_clarify=False,
            template_key=intent.value,
            decision_reason="Financial analysis requires verified FinanceEngine metrics"
        )
