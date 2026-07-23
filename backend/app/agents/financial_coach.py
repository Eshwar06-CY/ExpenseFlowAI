"""
FinancialCoachAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine
from app.services.ai_financial_coach import AIFinancialCoachService


class FinancialCoachAgent(BaseAgent):
    name = "FinancialCoachAgent"
    description = "Specializes in holistic financial health scoring, savings rates, and lifestyle coaching."
    capabilities = ["financial_health_score", "savings_rate_optimization", "lifestyle_coaching"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Financial Coach Agent. Provide expert guidance on financial health and savings."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        coach_service = AIFinancialCoachService(provider=self.provider)
        report = coach_service.generate_coaching_report(db, user_id=user_id, period=period)
        return {
            "summary": report.get("summary", "Financial health evaluation complete."),
            "confidence": report.get("confidence", 0.95),
            "data": report
        }
