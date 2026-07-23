"""
TaxAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine


class TaxAgent(BaseAgent):
    name = "TaxAgent"
    description = "Specializes in tax deduction optimization, taxable income estimation, and tax-advantaged savings."
    capabilities = ["taxable_income_estimation", "deduction_tracking", "tax_advantaged_accounts"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Tax Agent. Provide tax optimization guidance and deduction tracking."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        annual_income = summary.get("period_income", 0.0) * 12.0

        return {
            "summary": f"Estimated annualized gross income subject to tax analysis: ${annual_income:,.2f}.",
            "confidence": 0.88,
            "data": {
                "annualized_income": annual_income,
                "suggested_deductions": ["Retirement contributions", "Health insurance premiums"]
            }
        }
