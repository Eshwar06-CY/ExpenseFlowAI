"""
BudgetAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine


class BudgetAgent(BaseAgent):
    name = "BudgetAgent"
    description = "Specializes in category budget caps, spending adherence tracking, and outflow reallocations."
    capabilities = ["budget_adherence", "category_caps", "expense_reallocation"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Budget Agent. Analyze category spending adherence and recommend optimal caps."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        adherence = FinanceEngine.get_budget_adherence(db, user_id=user_id)
        rate = adherence.get("adherence_rate_pct", 100.0)
        return {
            "summary": f"Overall category budget adherence rate is {rate:.1f}%.",
            "confidence": 0.95,
            "data": adherence
        }
