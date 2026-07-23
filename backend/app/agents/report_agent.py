"""
ReportAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.finance_engine import FinanceEngine


class ReportAgent(BaseAgent):
    name = "ReportAgent"
    description = "Specializes in executive financial summaries, trend charts synthesis, and exportable financial audits."
    capabilities = ["executive_summaries", "trend_synthesis", "financial_audits"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Report Agent. Synthesize clean executive financial audit reports."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        return {
            "summary": f"Comprehensive financial report compiled for period '{period}'.",
            "confidence": 0.98,
            "data": summary
        }
