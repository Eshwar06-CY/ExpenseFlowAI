"""
Prompt Builder for ExpenseFlowAI AI Financial Advisor - Multi-Stage Reasoning Architecture

Integrates IntentClassifier, EntityExtractor, TaskPlanner, DecisionEngine,
ConversationManager, and PromptSelector into a cohesive AI reasoning pipeline.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from app.ai.intent_classifier import IntentClassifier, IntentResult, IntentType
from app.ai.entity_extractor import EntityExtractor, ExtractedEntities
from app.ai.task_planner import TaskPlanner, TaskPlan
from app.ai.decision_engine import DecisionEngine, DecisionResult
from app.ai.conversation_manager import ConversationManager
from app.ai.prompt_templates import PromptSelector, FINANCIAL_ANALYSIS_SYSTEM_PROMPT
from app.ai.insight_rules import InsightRuleEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    intent_result: IntentResult
    entities: ExtractedEntities
    task_plan: TaskPlan
    decision: DecisionResult
    system_prompt: str
    prompt_text: str
    is_clarification: bool


class PromptBuilder:
    @staticmethod
    def build_financial_context(financial_summary: Dict[str, Any]) -> str:
        """
        Formats financial metrics and rule engine insights into structured markdown text.
        """
        if not financial_summary:
            return ""

        total_balance = financial_summary.get("total_balance", 0.0)
        period = financial_summary.get("period", "30d")
        period_income = financial_summary.get("period_income", 0.0)
        period_expense = financial_summary.get("period_expense", 0.0)
        period_savings = financial_summary.get("period_savings", 0.0)
        savings_rate = financial_summary.get("period_savings_rate", 0.0)
        health_score = financial_summary.get("health_score", 0)
        health_status = financial_summary.get("health_status", "N/A")

        category_spending: List[Dict[str, Any]] = financial_summary.get("category_spending", [])
        health_metrics: Dict[str, Any] = financial_summary.get("health_metrics", {})

        top_categories_str = "None recorded"
        if category_spending:
            cat_lines = [
                f"  - {c.get('category', 'General')}: ${c.get('amount', 0.0):,.2f} ({c.get('percentage', 0.0):.1f}%)"
                for c in category_spending[:5]
            ]
            top_categories_str = "\n".join(cat_lines)

        reserve_months = health_metrics.get("reserve_months", 0.0)
        budget_adherence = health_metrics.get("budget_adherence_pct", 100.0)
        bill_reliability = health_metrics.get("bill_reliability_pct", 100.0)

        # Evaluate Rule Engine insights
        insights = InsightRuleEngine.evaluate_rules(financial_summary)
        insight_lines = [f"  - [{i.severity.upper()}] {i.title}: {i.details}" for i in insights]
        insights_str = "\n".join(insight_lines) if insight_lines else "None"

        context = f"""
VERIFIED FINANCIAL METRICS (Source: ExpenseFlowAI FinanceEngine):
-------------------------------------------------------------
- Total Available Balance: ${total_balance:,.2f}
- Active Analysis Window: {period}
- Total Income ({period}): ${period_income:,.2f}
- Total Expenses ({period}): ${period_expense:,.2f}
- Net Savings ({period}): ${period_savings:,.2f}
- Savings Rate: {savings_rate:.1f}%
- Financial Health Score: {health_score}/100 ({health_status})
- Emergency Cash Reserve: {reserve_months:.1f} months of expenses
- Budget Adherence Rate: {budget_adherence:.1f}%
- Bill Payment Reliability: {bill_reliability:.1f}%

Top Spending Categories ({period}):
{top_categories_str}

VERIFIED RULE ENGINE INSIGHTS (Source: InsightRuleEngine):
{insights_str}
-------------------------------------------------------------
Instructions for AI Provider:
1. Explain and expand on the above verified insights in compassionate natural language.
2. DO NOT recalculate or modify any financial numbers.
"""
        return context.strip()

    @classmethod
    def run_pipeline(
        cls,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        financial_summary: Optional[Dict[str, Any]] = None,
        memories: Optional[List[Any]] = None,
        personalization_context: Optional[str] = None
    ) -> PipelineContext:
        """
        Runs full Multi-Stage Reasoning Pipeline and returns PipelineContext.
        """
        # 1. Intent Classification
        intent_res = IntentClassifier.classify(user_message, chat_history)

        # 2. Entity Extraction
        entities = EntityExtractor.extract(user_message, chat_history)

        # 3. Task Planning & Missing Info Detection
        task_plan = TaskPlanner.plan_task(intent_res, entities, financial_summary)

        # 4. Decision Engine
        decision = DecisionEngine.evaluate(intent_res, entities, task_plan)

        # 5. System Prompt & Conversation History Selection
        system_prompt = PromptSelector.get_system_prompt_for_intent(intent_res.intent)
        history_block = ConversationManager.format_history_block(chat_history)

        # Handle Missing Info Clarification Decision
        if decision.should_clarify and task_plan.clarification_prompt:
            logger.info("[PromptBuilder] Pipeline selected CLARIFICATION path")
            return PipelineContext(
                intent_result=intent_res,
                entities=entities,
                task_plan=task_plan,
                decision=decision,
                system_prompt=system_prompt,
                prompt_text=task_plan.clarification_prompt,
                is_clarification=True
            )

        # Non-Financial Intents (Greetings, Small Talk, Identity, Help, Jokes)
        if not decision.use_finance_engine:
            prompt_text = f"{history_block}USER MESSAGE:\n{user_message}\n\nASSISTANT RESPONSE:"
            return PipelineContext(
                intent_result=intent_res,
                entities=entities,
                task_plan=task_plan,
                decision=decision,
                system_prompt=system_prompt,
                prompt_text=prompt_text,
                is_clarification=False
            )

        # Financial Intents with Complete Data
        context_block = ""
        if financial_summary:
            context_block = cls.build_financial_context(financial_summary) + "\n\n"

        pers_block = f"{personalization_context.strip()}\n\n" if personalization_context else ""

        memory_block = ""
        if memories:
            mem_lines = []
            for m in memories[:10]:
                if hasattr(m, "category") and hasattr(m, "key") and hasattr(m, "value"):
                    mem_lines.append(f"  - [{m.category}] {m.key}: {m.value}")
                elif isinstance(m, dict):
                    mem_lines.append(f"  - [{m.get('category', 'note')}] {m.get('key', 'info')}: {m.get('value', '')}")
            if mem_lines:
                memory_block = "PERSISTENT USER MEMORIES & PREFERENCES:\n" + "\n".join(mem_lines) + "\n\n"

        prompt_text = f"{context_block}{pers_block}{memory_block}{history_block}USER QUESTION:\n{user_message}\n\nADVISOR RESPONSE:"
        return PipelineContext(
            intent_result=intent_res,
            entities=entities,
            task_plan=task_plan,
            decision=decision,
            system_prompt=system_prompt,
            prompt_text=prompt_text,
            is_clarification=False
        )

    @classmethod
    def build_prompt(
        cls,
        financial_summary: Optional[Dict[str, Any]] = None,
        user_message: str = "",
        chat_history: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[Any]] = None,
        personalization_context: Optional[str] = None
    ) -> str:
        pipeline = cls.run_pipeline(
            user_message=user_message,
            chat_history=chat_history,
            financial_summary=financial_summary,
            memories=memories,
            personalization_context=personalization_context
        )
        return pipeline.prompt_text

    @classmethod
    def get_system_prompt_for_message(
        cls,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        intent_res = IntentClassifier.classify(user_message, chat_history)
        return PromptSelector.get_system_prompt_for_intent(intent_res.intent)

    @staticmethod
    def get_system_prompt() -> str:
        return FINANCIAL_ANALYSIS_SYSTEM_PROMPT
