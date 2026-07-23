"""
Financial Digital Twin & Simulation Engine Service - ExpenseFlowAI

Creates an in-memory virtual replica of the user's financial state to safely simulate
"what-if" scenarios (large purchases, salary changes, job loss, emergency expenses)
WITHOUT modifying production database records.
FinanceEngine remains the calculation foundation.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.finance_engine import FinanceEngine
from app.models.bill import Bill
from app.models.goal import Goal
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


DIGITAL_TWIN_PROMPT_TEMPLATE = """You are ExpenseFlowAI Financial Digital Twin Simulator.
Explain the simulated impact of the user's 'what-if' financial decision based on the virtual state model.

SIMULATION SCENARIO: {scenario_title}
- Baseline Liquid Balance: ${balance_before:,.2f} -> Simulated Balance: ${balance_after:,.2f}
- Baseline Monthly Net Savings: ${savings_before:,.2f} -> Simulated Monthly Savings: ${savings_after:,.2f}
- Baseline Emergency Reserve: {reserve_before:.1f} months -> Simulated Reserve: {reserve_after:.1f} months
- Financial Health Score: {health_before}/100 -> {health_after}/100
- Financial Survival Runway: {survival_months} month(s)

RULES:
1. Explain the immediate and long-term consequences of this scenario.
2. Provide survival analysis if income is lost or expenses exceed income.
3. Recommend specific steps to mitigate risks or maximize benefits.
4. Keep the explanation professional, actionable, and structured.
"""


class DigitalTwinService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def get_baseline_twin_state(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Returns the current virtual snapshot of the user's digital twin.
        """
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period="30d")
        total_balance = summary.get("total_balance", 0.0)
        income = summary.get("period_income", 0.0)
        expense = summary.get("period_expense", 0.0)
        savings = summary.get("period_savings", 0.0)
        health_score = summary.get("health_score", 0)
        health_status = summary.get("health_status", "N/A")

        goals_count = db.query(Goal).filter(Goal.user_id == user_id).count()
        bills_count = db.query(Bill).filter(Bill.user_id == user_id, Bill.is_paid == False).count()

        return {
            "user_id": user_id,
            "total_balance": total_balance,
            "monthly_income": income,
            "monthly_expenses": expense,
            "monthly_savings": savings,
            "health_score": health_score,
            "health_status": health_status,
            "active_goals_count": goals_count,
            "unpaid_bills_count": bills_count
        }

    def simulate_scenario(
        self,
        db: Session,
        user_id: int,
        scenario_type: str,
        amount: float = 0.0,
        percentage_change: float = 0.0,
        duration_months: int = 1,
        description: Optional[str] = None,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Performs in-memory simulation of a what-if financial scenario.
        GUARANTEES ZERO MODIFICATIONS to production database tables.
        """
        # 1. Fetch baseline metrics from FinanceEngine
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        health_data = FinanceEngine.calculate_financial_health_score(db, user_id=user_id)

        bal_before = float(summary.get("total_balance", 0.0))
        inc_before = float(summary.get("period_income", 0.0))
        exp_before = float(summary.get("period_expense", 0.0))
        sav_before = float(summary.get("period_savings", 0.0))
        health_before = health_data["health_score"]
        reserve_before = float(health_data["metrics"]["reserve_months"])

        # 2. Setup Virtual Simulation State (In-Memory Copies)
        bal_after = bal_before
        inc_after = inc_before
        exp_after = exp_before

        scenario_name = description or f"{scenario_type} Scenario"

        # 3. Apply Virtual What-If Logic
        st_upper = scenario_type.upper()
        if st_upper == "LARGE_PURCHASE":
            bal_after -= amount
            if not description:
                scenario_name = f"Large Purchase (${amount:,.2f})"

        elif st_upper == "SALARY_CHANGE":
            pct = percentage_change if percentage_change != 0 else (10.0 if amount > 0 else -10.0)
            inc_delta = inc_before * (pct / 100.0)
            inc_after += inc_delta
            if not description:
                scenario_name = f"Salary Change ({pct:+.1f}%)"

        elif st_upper == "JOB_LOSS":
            inc_after = 0.0
            if not description:
                scenario_name = f"Job Loss for {duration_months} Month(s)"

        elif st_upper == "BONUS":
            bal_after += amount
            if not description:
                scenario_name = f"Lump Sum Bonus (${amount:,.2f})"

        elif st_upper == "EXPENSE_INCREASE":
            exp_after += amount
            if not description:
                scenario_name = f"Expense Increase (${amount:,.2f}/mo)"

        elif st_upper == "CUSTOM":
            if amount != 0:
                bal_after -= amount
            if percentage_change != 0:
                inc_after *= (1.0 + percentage_change / 100.0)

        # 4. Calculate Simulated Metrics
        sav_after = round(inc_after - exp_after, 2)
        reserve_after = round(max(0.0, bal_after) / max(exp_after, 1.0), 2)

        # Survival runway calculation
        if inc_after >= exp_after:
            survival_months = 999.0  # Sustainable indefinite cashflow
        else:
            monthly_deficit = exp_after - inc_after
            survival_months = round(max(0.0, bal_after) / max(monthly_deficit, 1.0), 1)

        # 5. Compute Simulated Health Score
        sav_rate_after = (sav_after / max(inc_after, 1.0) * 100.0) if inc_after > 0 else 0.0
        score_sav = min(max((sav_rate_after / 20.0) * 25.0, 0.0), 25.0)
        score_res = min(max((reserve_after / 6.0) * 25.0, 0.0), 25.0)
        score_bud = health_data["components"]["budget_score"]
        score_bill = health_data["components"]["bill_score"]
        score_goal = health_data["components"]["goal_score"]

        raw_health = score_sav + score_res + score_bud + score_bill + score_goal
        if bal_after < 0:
            raw_health -= 25.0

        health_after = int(round(min(100.0, max(0.0, raw_health))))

        # 6. Generate Recommendations
        recommendations = []
        if bal_after < 0:
            recommendations.append(f"CRITICAL: Avoid scenario or secure additional liquid funding (${abs(bal_after):,.2f} deficit).")
        if survival_months < 6 and st_upper == "JOB_LOSS":
            recommendations.append(f"Cut discretionary spending by {min(30, int((exp_after * 0.3)))}% to extend survival runway.")
        if sav_after > sav_before:
            recommendations.append(f"Automate surplus transfer of ${sav_after * 0.5:,.2f}/mo into high-yield emergency reserve.")
        if health_after < health_before:
            recommendations.append("Build emergency buffer to offset reduced health rating.")
        if not recommendations:
            recommendations.append("Scenario is financially sustainable within your current risk tolerance.")

        # 7. AI Executive Narrative Explanation
        prompt = DIGITAL_TWIN_PROMPT_TEMPLATE.format(
            scenario_title=scenario_name,
            balance_before=bal_before, balance_after=bal_after,
            savings_before=sav_before, savings_after=sav_after,
            reserve_before=reserve_before, reserve_after=reserve_after,
            health_before=health_before, health_after=health_after,
            survival_months="Indefinite" if survival_months == 999.0 else f"{survival_months:.1f}"
        )

        try:
            explanation = self.provider.generate(prompt=prompt)
            if not explanation or len(explanation.strip()) < 10:
                explanation = self._build_deterministic_explanation(scenario_name, health_before, health_after, survival_months, bal_after)
        except Exception as exc:
            logger.warning("LLM Digital Twin simulation error (%s). Using fallback explanation.", str(exc))
            explanation = self._build_deterministic_explanation(scenario_name, health_before, health_after, survival_months, bal_after)

        impact_metrics = {
            "balance_before": round(bal_before, 2),
            "balance_after": round(bal_after, 2),
            "monthly_savings_before": round(sav_before, 2),
            "monthly_savings_after": round(sav_after, 2),
            "reserve_months_before": round(reserve_before, 2),
            "reserve_months_after": round(reserve_after, 2),
            "survival_months": survival_months
        }

        return {
            "scenario": scenario_name,
            "impact": impact_metrics,
            "financial_health_before": health_before,
            "financial_health_after": health_after,
            "recommendations": recommendations,
            "explanation": explanation
        }

    def _build_deterministic_explanation(
        self,
        scenario_name: str,
        health_before: int,
        health_after: int,
        survival_months: float,
        bal_after: float
    ) -> str:
        health_delta = health_after - health_before
        direction = "improves" if health_delta >= 0 else "decreases"
        runway_text = "indefinite" if survival_months == 999.0 else f"{survival_months:.1f} months"

        return (
            f"Under the '{scenario_name}' simulation, your liquid balance is projected at ${bal_after:,.2f}. "
            f"Your financial health score {direction} from {health_before}/100 to {health_after}/100. "
            f"Your estimated financial survival runway is {runway_text}. "
            f"All simulation calculations are virtual; production database records remain untouched."
        )
