"""
FinancialReviewWorkflow - ExpenseFlowAI Autonomous Workflow Engine
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.services.finance_engine import FinanceEngine


class FinancialReviewWorkflow(BaseWorkflow):
    name = "FinancialReviewWorkflow"
    description = "Autonomous Financial Review: Pulls period metrics, analyzes health score, and compiles monthly executive briefing."

    def _setup_steps(self):
        self.steps = [
            WorkflowStep("Pull Dashboard Summary", self._step_pull_summary),
            WorkflowStep("Compile Executive Review", self._step_compile_review),
        ]

    def _step_pull_summary(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=ctx.get("period", "30d"))
        return {
            "recommendation": f"Fetched period financial metrics. Health score: {summary.get('health_score', 0)}/100.",
            "context_update": {"summary": summary}
        }

    def _step_compile_review(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        summary = ctx.get("summary", {})
        return {
            "action": {"type": "GENERATE_REVIEW_REPORT", "health_status": summary.get("health_status", "N/A")},
            "next_step": "Download monthly executive PDF report from Reports portal."
        }
