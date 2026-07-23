"""
AI Tool Registry & Isolated Tool Services - ExpenseFlowAI

Defines isolated tool classes (BudgetTool, GoalTool, ExpenseTool, ReminderTool, ReportTool)
that execute safe application actions through existing services & ORM models.

The LLM NEVER accesses the database directly. Tools validate inputs and execute backend logic.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.services.finance_engine import FinanceEngine

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    name: str = "BaseTool"
    description: str = "Base tool interface"

    @abstractmethod
    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def is_destructive(self, action: str) -> bool:
        """
        Returns True if the action is destructive (e.g. delete, transfer, reset, bulk_delete).
        """
        return action.lower() in {"delete", "delete_subscription", "delete_budget", "delete_goal", "transfer", "reset", "bulk_delete"}


class BudgetTool(BaseTool):
    name = "BudgetTool"
    description = "Manages category spending budgets (create, update, list)"

    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        cat_name = str(parameters.get("category", parameters.get("category_name", "General")))
        amount = float(parameters.get("amount", 0.0))

        # Find or create Category
        stmt_cat = select(Category).where(and_(Category.user_id == user_id, Category.name == cat_name))
        cat = db.execute(stmt_cat).scalar_one_or_none()
        if not cat:
            cat = Category(user_id=user_id, name=cat_name, type="expense", color="#4F46E5")
            db.add(cat)
            db.commit()
            db.refresh(cat)

        month_str = datetime.now(timezone.utc).strftime("%Y-%m")

        stmt_b = select(Budget).where(and_(Budget.user_id == user_id, Budget.category_id == cat.id, Budget.month == month_str))
        budget = db.execute(stmt_b).scalar_one_or_none()

        if action in {"create_budget", "update_budget", "set_budget"}:
            if budget:
                budget.amount = amount
            else:
                budget = Budget(user_id=user_id, category_id=cat.id, amount=amount, spent=0.0, month=month_str)
                db.add(budget)
            db.commit()
            db.refresh(budget)
            return {
                "action": action,
                "category": cat_name,
                "amount": amount,
                "budget_id": budget.id,
                "message": f"Successfully set budget for '{cat_name}' to ${amount:,.2f}."
            }
        elif action == "list_budgets":
            budgets = FinanceEngine.get_budget_adherence(db, user_id=user_id)
            return {"action": action, "budgets": budgets.get("budgets", [])}

        raise ValueError(f"Unknown BudgetTool action: {action}")


class GoalTool(BaseTool):
    name = "GoalTool"
    description = "Manages savings goals (create, list)"

    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        goal_name = str(parameters.get("goal_name", parameters.get("name", "Goal")))
        target_amount = float(parameters.get("target_amount", parameters.get("amount", 0.0)))
        current_saved = float(parameters.get("current_saved", parameters.get("current_amount", 0.0)))

        if action in {"create_goal", "set_goal"}:
            goal = Goal(
                user_id=user_id,
                name=goal_name,
                target_amount=target_amount,
                current_amount=current_saved
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)
            return {
                "action": action,
                "goal_id": goal.id,
                "goal_name": goal_name,
                "target_amount": target_amount,
                "current_saved": current_saved,
                "message": f"Created goal '{goal_name}' with target ${target_amount:,.2f}."
            }
        elif action == "list_goals":
            goals = db.execute(select(Goal).where(Goal.user_id == user_id)).scalars().all()
            return {
                "action": action,
                "goals": [{"id": g.id, "name": g.name, "target_amount": g.target_amount, "current_amount": g.current_amount} for g in goals]
            }

        raise ValueError(f"Unknown GoalTool action: {action}")


class ExpenseTool(BaseTool):
    name = "ExpenseTool"
    description = "Inspects subscriptions and handles deletion requests"

    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action == "list_subscriptions":
            min_amount = float(parameters.get("min_amount", 0.0))
            bills = db.execute(select(Bill).where(Bill.user_id == user_id)).scalars().all()
            filtered = [
                {"id": b.id, "name": b.name, "amount": b.amount, "is_paid": b.is_paid}
                for b in bills if b.amount >= min_amount
            ]
            return {"action": action, "min_amount": min_amount, "subscriptions": filtered}

        elif action in {"delete_subscription", "delete"}:
            sub_id = parameters.get("subscription_id", parameters.get("id"))
            sub_name = parameters.get("subscription_name", parameters.get("name"))

            stmt = select(Bill).where(Bill.user_id == user_id)
            if sub_id:
                stmt = stmt.where(Bill.id == int(sub_id))
            elif sub_name:
                stmt = stmt.where(Bill.name.ilike(f"%{sub_name}%"))

            bill = db.execute(stmt).scalars().first()
            if not bill:
                return {"action": action, "found": False, "message": f"Subscription '{sub_name or sub_id}' not found."}

            db.delete(bill)
            db.commit()
            return {"action": action, "deleted_id": bill.id, "deleted_name": bill.name, "message": f"Successfully deleted subscription '{bill.name}'."}

        raise ValueError(f"Unknown ExpenseTool action: {action}")


class ReminderTool(BaseTool):
    name = "ReminderTool"
    description = "Sets recurring or one-time payment reminders"

    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        title = str(parameters.get("title", parameters.get("name", "Reminder")))
        amount = float(parameters.get("amount", 0.0))

        if action in {"create_reminder", "set_reminder"}:
            now = datetime.now(timezone.utc)
            bill = Bill(
                user_id=user_id,
                name=title,
                amount=amount,
                due_date=now,
                is_paid=False
            )
            db.add(bill)
            db.commit()
            db.refresh(bill)
            return {
                "action": action,
                "reminder_id": bill.id,
                "title": title,
                "amount": amount,
                "message": f"Set reminder for '{title}' (${amount:,.2f})."
            }

        raise ValueError(f"Unknown ReminderTool action: {action}")


class ReportTool(BaseTool):
    name = "ReportTool"
    description = "Fetches comprehensive financial summary reports"

    def execute(self, db: Session, user_id: int, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        period = str(parameters.get("period", "30d"))
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)
        return {"action": action, "report": summary}


class ToolRegistry:
    _tools: Dict[str, BaseTool] = {
        "BudgetTool": BudgetTool(),
        "GoalTool": GoalTool(),
        "ExpenseTool": ExpenseTool(),
        "ReminderTool": ReminderTool(),
        "ReportTool": ReportTool(),
    }

    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[BaseTool]:
        return cls._tools.get(tool_name)

    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        return [
            {"name": name, "description": tool.description}
            for name, tool in cls._tools.items()
        ]
