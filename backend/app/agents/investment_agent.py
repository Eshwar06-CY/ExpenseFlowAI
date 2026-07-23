"""
InvestmentAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine


class InvestmentAgent(BaseAgent):
    name = "InvestmentAgent"
    description = "Specializes in surplus cash deployment, risk-adjusted portfolio allocation, and compounding returns."
    capabilities = ["portfolio_allocation", "surplus_deployment", "compound_growth"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Investment Agent. Recommend safe surplus deployment strategies."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        surplus = summary.get("period_savings", 0.0)
        investable = max(surplus * 0.5, 0.0)

        return {
            "summary": f"Estimated investable monthly surplus is ${investable:,.2f}.",
            "confidence": 0.90,
            "data": {
                "investable_surplus": investable,
                "allocation": {"index_funds": "60%", "debt_bonds": "30%", "liquid_cash": "10%"}
            }
        }
