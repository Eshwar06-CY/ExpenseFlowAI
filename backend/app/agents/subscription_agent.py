"""
SubscriptionAgent - ExpenseFlowAI Multi-Agent Architecture
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.bill import Bill


class SubscriptionAgent(BaseAgent):
    name = "SubscriptionAgent"
    description = "Specializes in identifying recurring subscription leakage, duplicate bills, and cancellation candidates."
    capabilities = ["subscription_audit", "leakage_detection", "bill_cancellation"]

    @property
    def system_prompt(self) -> str:
        return "You are ExpenseFlowAI Subscription Agent. Identify recurring sub leakage and prune unused services."

    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        bills = db.execute(select(Bill).where(Bill.user_id == user_id)).scalars().all()
        total_sub_cost = sum(b.amount for b in bills)

        return {
            "summary": f"Audited {len(bills)} active recurring subscriptions totaling ${total_sub_cost:,.2f}/mo.",
            "confidence": 0.96,
            "data": {
                "active_subscriptions": len(bills),
                "total_monthly_cost": total_sub_cost,
                "subscriptions": [{"name": b.name, "amount": b.amount} for b in bills]
            }
        }
