"""
ExpenseReductionWorkflow - ExpenseFlowAI Autonomous Workflow Engine
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.services.finance_engine import FinanceEngine
from app.models.bill import Bill


class ExpenseReductionWorkflow(BaseWorkflow):
    name = "ExpenseReductionWorkflow"
    description = "Autonomous Expense Reduction: Finds expensive categories, audits subscriptions, and generates an action checklist."

    def _setup_steps(self):
        self.steps = [
            WorkflowStep("Find Expensive Categories", self._step_find_expensive_categories),
            WorkflowStep("Audit Recurring Subscriptions", self._step_audit_subscriptions),
            WorkflowStep("Generate Action Checklist", self._step_generate_checklist),
        ]

    def _step_find_expensive_categories(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        spending = FinanceEngine.get_category_spending(db, user_id=user_id)
        top_cats = [c["category"] for c in spending[:2]]
        return {
            "recommendation": f"Top spending categories identified: {', '.join(top_cats) if top_cats else 'None'}.",
            "context_update": {"top_categories": top_cats}
        }

    def _step_audit_subscriptions(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        bills = db.execute(select(Bill).where(Bill.user_id == user_id)).scalars().all()
        total_bills = sum(b.amount for b in bills)
        return {
            "action": {"type": "AUDIT_SUBSCRIPTIONS", "count": len(bills), "total_cost": total_bills},
            "recommendation": f"Audited {len(bills)} active recurring payments (${total_bills:,.2f}/mo).",
            "context_update": {"bill_count": len(bills)}
        }

    def _step_generate_checklist(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "next_step": "1. Cancel unused streaming subscriptions. 2. Set food delivery cap to $200/mo. 3. Re-evaluate energy utility plans."
        }
