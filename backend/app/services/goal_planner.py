"""
AI Goal Planner Service - ExpenseFlowAI

Evaluates target financial goals (e.g. MacBook Pro, Emergency Savings, Trip) against
verified cashflow metrics sourced from FinanceEngine. Computes required contribution
rates, completion timelines, and success probabilities.

The AI DOES NOT perform mathematical time-value calculations. Baseline calculations
(surplus, months needed, required rate) are computed directly from FinanceEngine data.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.finance_engine import FinanceEngine
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.schemas.goals import GoalFeasibilityStatus

logger = logging.getLogger(__name__)


GOAL_SYSTEM_PROMPT = """You are ExpenseFlowAI Goal Planner. You evaluate financial goals based on verified user cashflow data and pre-calculated target timelines.

RULES:
1. USE ONLY THE SUPPLIED FINANCIAL DATA: Do not invent income or savings figures.
2. OUTPUT STRICT JSON ONLY: You MUST respond with a single valid JSON object containing:
   - "status": "ON_TRACK", "FEASIBLE_WITH_ADJUSTMENTS", "HIGH_RISK", "UNFEASIBLE", or "ALREADY_ACHIEVED".
   - "completion_probability": number between 0.0 and 1.0.
   - "recommendations": array of 2-3 actionable advice steps.
   - "risks": array of 1-2 potential risk factors.
   - "summary": a brief 1-2 sentence executive assessment.
"""


class AIGoalPlannerService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def evaluate_goal(
        self,
        db: Session,
        user_id: int,
        goal_name: str,
        target_amount: float,
        target_date: Optional[str] = None,
        current_saved: float = 0.0
    ) -> Dict[str, Any]:
        """
        Retrieves cashflow metrics from FinanceEngine, calculates timeline feasibility,
        enriches with LLM recommendations, and falls back safely to deterministic rules.
        """
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period="30d")

        period_income = summary.get("period_income", 0.0)
        period_expense = summary.get("period_expense", 0.0)
        period_savings = summary.get("period_savings", 0.0)
        monthly_surplus = max(period_savings, 0.0)

        remaining_needed = max(target_amount - current_saved, 0.0)
        now = datetime.now(timezone.utc)

        # Baseline calculations
        if remaining_needed <= 0:
            return {
                "goal_name": goal_name,
                "target_amount": target_amount,
                "current_saved": current_saved,
                "monthly_required": 0.0,
                "monthly_surplus": monthly_surplus,
                "status": GoalFeasibilityStatus.ALREADY_ACHIEVED.value,
                "completion_probability": 1.0,
                "estimated_completion_date": now.strftime("%Y-%m-%d"),
                "months_to_complete": 0.0,
                "recommendations": ["Goal requirement is already fully accumulated!"],
                "risks": [],
                "summary": f"Congratulations! You have already accumulated enough to fulfill your target goal of ${target_amount:,.2f}."
            }

        # Calculate target months if target_date provided
        target_months = None
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                diff_days = (target_dt - now).days
                target_months = max(diff_days / 30.4375, 0.1)
            except ValueError:
                target_months = None

        monthly_required = remaining_needed / (target_months if target_months else 12.0)

        # Compute baseline timeline & feasibility
        if monthly_surplus <= 0:
            months_to_complete = 999.0
            est_completion_date = "Uncertain"
            base_status = GoalFeasibilityStatus.UNFEASIBLE.value
            base_prob = 0.05
        else:
            months_to_complete = remaining_needed / monthly_surplus
            est_completion_dt = now + timedelta(days=int(months_to_complete * 30.4375))
            est_completion_date = est_completion_dt.strftime("%Y-%m-%d")

            if target_months:
                ratio = months_to_complete / target_months
                if ratio <= 1.0:
                    base_status = GoalFeasibilityStatus.ON_TRACK.value
                    base_prob = round(min(0.98, max(0.75, 1.0 - 0.15 * (ratio - 0.5))), 2)
                elif ratio <= 1.5:
                    base_status = GoalFeasibilityStatus.FEASIBLE_WITH_ADJUSTMENTS.value
                    base_prob = 0.65
                else:
                    base_status = GoalFeasibilityStatus.HIGH_RISK.value
                    base_prob = 0.35
            else:
                base_status = GoalFeasibilityStatus.ON_TRACK.value if months_to_complete <= 36 else GoalFeasibilityStatus.FEASIBLE_WITH_ADJUSTMENTS.value
                base_prob = 0.90

        context = {
            "goal_name": goal_name,
            "target_amount": target_amount,
            "current_saved": current_saved,
            "remaining_needed": remaining_needed,
            "monthly_surplus": monthly_surplus,
            "monthly_required": monthly_required,
            "target_date": target_date,
            "estimated_completion_date": est_completion_date,
            "months_to_complete": round(months_to_complete, 1),
            "base_status": base_status,
            "base_prob": base_prob
        }

        # Attempt LLM Enrichment
        prompt = self._build_goal_prompt(context)
        try:
            llm_response = self.provider.generate(prompt=prompt, system_prompt=GOAL_SYSTEM_PROMPT)
            parsed_json = self._extract_json(llm_response)
            if parsed_json:
                return {
                    "goal_name": goal_name,
                    "target_amount": target_amount,
                    "current_saved": current_saved,
                    "monthly_required": round(monthly_required, 2),
                    "monthly_surplus": round(monthly_surplus, 2),
                    "status": str(parsed_json.get("status", base_status)),
                    "completion_probability": float(parsed_json.get("completion_probability", base_prob)),
                    "estimated_completion_date": est_completion_date,
                    "months_to_complete": round(months_to_complete, 1),
                    "recommendations": self._ensure_list(parsed_json.get("recommendations"), self._default_recommendations(context)),
                    "risks": self._ensure_list(parsed_json.get("risks"), self._default_risks(context)),
                    "summary": str(parsed_json.get("summary", self._default_summary(context))),
                }
        except Exception as exc:
            logger.warning("LLM goal planning failed (%s). Using deterministic fallback.", str(exc))

        # Deterministic Fallback if LLM unavailable
        return {
            "goal_name": goal_name,
            "target_amount": target_amount,
            "current_saved": current_saved,
            "monthly_required": round(monthly_required, 2),
            "monthly_surplus": round(monthly_surplus, 2),
            "status": base_status,
            "completion_probability": base_prob,
            "estimated_completion_date": est_completion_date,
            "months_to_complete": round(months_to_complete, 1),
            "recommendations": self._default_recommendations(context),
            "risks": self._default_risks(context),
            "summary": self._default_summary(context),
        }

    def _build_goal_prompt(self, ctx: Dict[str, Any]) -> str:
        return f"""
Goal Context (Source: FinanceEngine):
- Goal Name: {ctx['goal_name']}
- Target Amount: ${ctx['target_amount']:,.2f}
- Current Accumulated Saved: ${ctx['current_saved']:,.2f}
- Remaining Amount Needed: ${ctx['remaining_needed']:,.2f}
- Verified Monthly Net Surplus: ${ctx['monthly_surplus']:,.2f}
- Monthly Contribution Required for Target Date: ${ctx['monthly_required']:,.2f}
- Target Date: {ctx['target_date'] or 'Not specified'}
- Calculated Timeline: ~{ctx['months_to_complete']} months (Est Completion: {ctx['estimated_completion_date']})
- Initial Feasibility Status: {ctx['base_status']} (Prob: {ctx['base_prob']})

Generate JSON goal evaluation object.
"""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    def _ensure_list(self, val: Any, default_list: List[str]) -> List[str]:
        if isinstance(val, list) and len(val) > 0:
            return [str(item) for item in val]
        return default_list

    def _default_summary(self, ctx: Dict[str, Any]) -> str:
        status = ctx["base_status"]
        months = ctx["months_to_complete"]
        if status == GoalFeasibilityStatus.UNFEASIBLE.value:
            return f"Your current net monthly surplus (${ctx['monthly_surplus']:,.2f}) is insufficient to reach '{ctx['goal_name']}'."
        return f"Reaching '{ctx['goal_name']}' is estimated to take {months:.1f} months at your current monthly surplus of ${ctx['monthly_surplus']:,.2f}."

    def _default_recommendations(self, ctx: Dict[str, Any]) -> List[str]:
        recs = []
        surplus = ctx["monthly_surplus"]
        required = ctx["monthly_required"]
        if surplus <= 0:
            recs.append("Cut non-essential discretionary expenses to generate a positive monthly net cashflow surplus.")
            recs.append("Consider extending your goal target deadline or scaling down the target cost.")
        elif surplus < required:
            diff = required - surplus
            recs.append(f"Increase monthly net savings by ${diff:,.2f}/mo to hit your desired target date.")
            recs.append("Automate monthly transfers to a dedicated savings sub-account.")
        else:
            recs.append(f"Set up an automated monthly transfer of ${required:,.2f} to guarantee target completion.")
            recs.append("Keep discretionary outflows steady to protect your monthly savings rate.")
        return recs

    def _default_risks(self, ctx: Dict[str, Any]) -> List[str]:
        risks = []
        if ctx["monthly_surplus"] <= 0:
            risks.append("Negative or zero monthly cashflow prevents any progress toward this goal.")
        elif ctx["months_to_complete"] > 24:
            risks.append("Long completion timeline (> 2 years) increases exposure to inflation and unexpected expenses.")
        else:
            risks.append("Sudden unexpected emergency expenses could delay the estimated completion date.")
        return risks
