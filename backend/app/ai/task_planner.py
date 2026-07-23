"""
Task Planner & Missing Information Detector - ExpenseFlowAI Multi-Stage Pipeline

Evaluates whether sufficient data exists to fulfill complex requests (such as financial goal roadmaps
or purchase affordability analysis). If information is missing, constructs an interactive clarification plan
to collect missing inputs before generating financial advice.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.ai.intent_classifier import IntentType, IntentResult
from app.ai.entity_extractor import ExtractedEntities

logger = logging.getLogger(__name__)


@dataclass
class TaskPlan:
    is_complete: bool
    intent: IntentType
    missing_fields: List[str] = field(default_factory=list)
    execution_steps: List[str] = field(default_factory=list)
    clarification_prompt: Optional[str] = None


class TaskPlanner:
    REQUIRED_GOAL_FIELDS = [
        "target_amount",
        "timeline_months",
        "monthly_income",
        "monthly_expenses",
        "current_savings"
    ]

    @classmethod
    def plan_task(
        cls,
        intent_result: IntentResult,
        entities: ExtractedEntities,
        finance_summary: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """
        Creates an internal execution plan and checks for missing information.
        """
        intent = intent_result.intent

        # 1. Non-complex intents (Greetings, Small Talk, Identity, Help, Spending Queries) are always complete
        if intent not in (IntentType.GOAL_PLANNING, IntentType.PURCHASE_DECISION, IntentType.SAVINGS_PLAN):
            return TaskPlan(
                is_complete=True,
                intent=intent,
                execution_steps=["Execute standard intent handler"]
            )

        # 2. Check available data from FinanceEngine summary
        summary = finance_summary or {}
        has_db_income = summary.get("period_income", 0.0) > 0
        has_db_expenses = summary.get("period_expense", 0.0) > 0
        has_db_balance = summary.get("total_balance", 0.0) > 0

        # Check missing fields
        missing = []
        if not entities.target_amount:
            missing.append("target_price_or_budget")
        if not entities.timeline_months:
            missing.append("purchase_timeline")
        if not entities.monthly_income and not has_db_income:
            missing.append("monthly_income")
        if not entities.monthly_expenses and not has_db_expenses:
            missing.append("monthly_expenses")
        if not entities.current_savings and not has_db_balance:
            missing.append("current_savings")

        # If key goal parameters are missing (e.g. user asks "Can I buy a bike?" without amount/timeline/income)
        if len(missing) >= 2 or not entities.target_amount:
            goal_desc = f"buying a {entities.goal_name or 'target item'}"
            if entities.target_amount:
                goal_desc += f" worth ${entities.target_amount:,.2f}"

            questions = []
            if not entities.target_amount:
                questions.append("Target price or budget (e.g. $2,000 or ₹2 lakh)?")
            if not entities.timeline_months:
                questions.append("Desired purchase timeline (e.g. 6 months, 2 years)?")
            if not entities.monthly_income and not has_db_income:
                questions.append("Monthly net income?")
            if not entities.monthly_expenses and not has_db_expenses:
                questions.append("Monthly living expenses?")
            if not entities.current_savings and not has_db_balance:
                questions.append("Current available savings & liquid reserves?")
            questions.append("Existing loans or active EMIs (if any)?")
            questions.append("Preferred payment mode (Cash vs. EMI)?")

            q_list_str = "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(questions)])

            clarification = f"""I'd love to help you build a personalized financial roadmap for **{goal_desc}**! 🎯

Before I generate a detailed affordability analysis and savings strategy, I need a few details:

{q_list_str}

Once you share these details, I'll calculate:
✔ Monthly savings target & timeline feasibility
✔ Budget optimization & expense caps
✔ Emergency fund protection buffer
✔ Cash vs. EMI comparison & risk analysis"""

            logger.info("[TaskPlanner] Created clarification plan for %s (Missing: %s)", intent.value, missing)
            return TaskPlan(
                is_complete=False,
                intent=intent,
                missing_fields=missing,
                execution_steps=["Ask clarification questions", "Wait for user response"],
                clarification_prompt=clarification
            )

        # Sufficient data available to execute plan
        steps = [
            f"Evaluate goal affordability for ${entities.target_amount:,.2f} over {entities.timeline_months or 12} months",
            "Calculate monthly required savings target",
            "Analyze impact on emergency reserve months",
            "Generate actionable purchase advice"
        ]
        return TaskPlan(
            is_complete=True,
            intent=intent,
            execution_steps=steps
        )
