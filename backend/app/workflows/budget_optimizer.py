"""
BudgetOptimizerWorkflow - ExpenseFlowAI Autonomous Workflow Engine
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.services.finance_engine import FinanceEngine


class BudgetOptimizerWorkflow(BaseWorkflow):
    name = "BudgetOptimizerWorkflow"
    description = "Autonomous Budget Optimizer: Analyzes category spending trends and auto-sets optimal category caps."

    def _setup_steps(self):
        self.steps = [
            WorkflowStep("Fetch Category Spending", self._step_fetch_category_spending),
            WorkflowStep("Recommend Category Caps", self._step_recommend_caps),
            WorkflowStep("Apply Budget Caps", self._step_apply_caps),
        ]

    def _step_fetch_category_spending(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        spending = FinanceEngine.get_category_spending(db, user_id=user_id)
        return {
            "recommendation": f"Analyzed spending across {len(spending)} categories.",
            "context_update": {"spending": spending}
        }

    def _step_recommend_caps(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        spending = ctx.get("spending", [])
        recs = [f"Cap '{c['category']}' at ${c['amount'] * 0.9:,.2f}" for c in spending[:3]]
        return {
            "recommendation": f"Recommended 10% trim across top categories: {', '.join(recs)}.",
            "context_update": {"recommendations_list": recs}
        }

    def _step_apply_caps(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": {"type": "AUTO_SET_BUDGETS", "applied": len(ctx.get("spending", []))},
            "next_step": "Monitor budget adherence notifications over the next 14 days."
        }
