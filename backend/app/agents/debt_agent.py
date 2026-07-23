"""
DebtAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine


class DebtAgent(BaseAgent):
    name = "DebtAgent"
    description = "Specializes in debt snowball/avalanche strategies, credit card payoff plans, and interest reduction."
    capabilities = ["debt_payoff_planning", "snowball_avalanche_strategy", "credit_health"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Debt Advisor Agent. Formulate optimal debt payoff plans to minimize interest."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        surplus = summary.get("period_savings", 0.0)

        payoff_allocation = max(surplus * 0.4, 0.0)
        return {
            "summary": f"Recommended monthly debt payoff allocation is ${payoff_allocation:,.2f} based on net surplus.",
            "confidence": 0.92,
            "data": {
                "monthly_surplus": surplus,
                "recommended_payoff_allocation": payoff_allocation,
                "strategy": "Avalanche Method (Pay highest APR first)"
            }
        }
