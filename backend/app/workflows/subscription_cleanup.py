"""
SubscriptionCleanupWorkflow - ExpenseFlowAI Autonomous Workflow Engine
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.models.bill import Bill


class SubscriptionCleanupWorkflow(BaseWorkflow):
    name = "SubscriptionCleanupWorkflow"
    description = "Autonomous Subscription Cleanup: Identifies unused or low-utilization subscriptions and stages pruning recommendations."

    def _setup_steps(self):
        self.steps = [
            WorkflowStep("Audit Subscriptions", self._step_audit),
            WorkflowStep("Stage Cancellation Recommendations", self._step_stage_cancellations),
        ]

    def _step_audit(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        bills = db.execute(select(Bill).where(Bill.user_id == user_id)).scalars().all()
        return {
            "recommendation": f"Identified {len(bills)} active recurring bill subscriptions.",
            "context_update": {"bills": [{"id": b.id, "name": b.name, "amount": b.amount} for b in bills]}
        }

    def _step_stage_cancellations(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        bills = ctx.get("bills", [])
        candidates = [b["name"] for b in bills if b["amount"] > 10.0]
        return {
            "action": {"type": "STAGE_CANCELLATION", "candidates": candidates},
            "recommendation": f"Staged cancellation candidates: {', '.join(candidates) if candidates else 'None'}.",
            "next_step": "Confirm cancellation for staged subscriptions via AI Action Center."
        }
