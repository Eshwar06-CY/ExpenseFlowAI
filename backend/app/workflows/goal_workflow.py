"""
GoalWorkflow - ExpenseFlowAI Autonomous Workflow Engine
"""

from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.services.finance_engine import FinanceEngine
from app.models.goal import Goal
from app.models.budget import Budget
from app.models.bill import Bill


class GoalWorkflow(BaseWorkflow):
    name = "GoalWorkflow"
    description = "Autonomous Multi-Step Goal Planner: Analyzes cashflow, creates goal, adjusts budgets, and schedules reminders."

    def _setup_steps(self):
        self.steps = [
            WorkflowStep("Analyze Cashflow", self._step_analyze_cashflow),
            WorkflowStep("Create Goal", self._step_create_goal, rollback_handler=self._rollback_create_goal),
            WorkflowStep("Adjust Budget", self._step_adjust_budget),
            WorkflowStep("Schedule Reminders", self._step_schedule_reminders),
        ]

    def _step_analyze_cashflow(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=ctx.get("period", "30d"))
        surplus = summary.get("period_savings", 0.0)
        return {
            "recommendation": f"Net monthly surplus identified: ${surplus:,.2f}.",
            "context_update": {"monthly_surplus": surplus}
        }

    def _step_create_goal(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        target_amount = float(ctx.get("target_amount", 50000.0))
        goal_name = str(ctx.get("goal_name", "Target Savings Goal"))

        goal = Goal(user_id=user_id, name=goal_name, target_amount=target_amount, current_amount=0.0)
        db.add(goal)
        db.commit()
        db.refresh(goal)

        return {
            "action": {"type": "CREATE_GOAL", "goal_id": goal.id, "name": goal_name, "amount": target_amount},
            "recommendation": f"Created goal '{goal_name}' for ${target_amount:,.2f}.",
            "context_update": {"created_goal_id": goal.id}
        }

    def _rollback_create_goal(self, db: Session, user_id: int, ctx: Dict[str, Any]):
        goal_id = ctx.get("created_goal_id")
        if goal_id:
            goal = db.get(Goal, goal_id)
            if goal:
                db.delete(goal)
                db.commit()

    def _step_adjust_budget(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        surplus = ctx.get("monthly_surplus", 0.0)
        monthly_contrib = max(surplus * 0.5, 500.0)
        return {
            "action": {"type": "ADJUST_BUDGET", "category": "Savings", "monthly_contribution": monthly_contrib},
            "recommendation": f"Allocated ${monthly_contrib:,.2f}/month towards target goal."
        }

    def _step_schedule_reminders(self, db: Session, user_id: int, ctx: Dict[str, Any]) -> Dict[str, Any]:
        bill = Bill(
            user_id=user_id,
            name=f"Goal Contribution: {ctx.get('goal_name', 'Goal')}",
            amount=500.0,
            due_date=datetime.now(timezone.utc),
            is_paid=False
        )
        db.add(bill)
        db.commit()
        return {
            "action": {"type": "SCHEDULE_REMINDER", "title": bill.name},
            "next_step": "Review monthly goal progress checkpoint on the 1st of every month."
        }
