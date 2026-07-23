"""
Smart Notification Engine & Service - ExpenseFlowAI

Provides notification generation, AI prioritization, deduplication, delivery preferences,
and lifecycle management for financial events across Budgets, Bills, Goals, Forecasts, AI Insights,
Security, and Achievements.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationPreference
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.services.finance_engine import FinanceEngine
from app.services.cashflow_forecast import CashFlowForecastService

logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    @classmethod
    def get_or_create_preferences(cls, db: Session, user_id: int) -> NotificationPreference:
        """
        Retrieves user notification preferences or creates default settings if none exist.
        """
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                enable_budget_alerts=True,
                enable_bill_reminders=True,
                enable_goal_updates=True,
                enable_forecast_warnings=True,
                enable_ai_recommendations=True,
                enable_security_alerts=True,
                enable_achievements=True,
                enable_email_notifications=True,
                enable_in_app=True,
                digest_frequency="weekly"
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @classmethod
    def update_preferences(cls, db: Session, user_id: int, updates: Dict[str, Any]) -> NotificationPreference:
        """
        Updates user notification preferences.
        """
        pref = cls.get_or_create_preferences(db, user_id)
        for key, val in updates.items():
            if hasattr(pref, key) and key not in ("id", "user_id", "created_at"):
                setattr(pref, key, val)
        pref.updated_at = datetime.now()
        db.commit()
        db.refresh(pref)
        return pref


class NotificationGenerator:
    @classmethod
    def generate_smart_notifications(cls, db: Session, user_id: int) -> List[Notification]:
        """
        Scans current financial state (Budgets, Bills, Goals, Forecasts, FinanceEngine)
        and creates prioritized, deduplicated notifications matching user preferences.
        """
        prefs = NotificationPreferenceService.get_or_create_preferences(db, user_id)
        if not prefs.enable_in_app:
            return []

        created_notifications: List[Notification] = []
        now = datetime.now()
        now_date = now.date()

        def is_duplicate(category: str, title: str) -> bool:
            """Checks if an identical notification was generated within the last 24 hours."""
            cutoff = now - timedelta(hours=24)
            existing = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.category == category,
                Notification.title == title,
                Notification.created_at >= cutoff
            ).first()
            return existing is not None

        # 1. Budget Alerts
        if prefs.enable_budget_alerts:
            budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
            for b in budgets:
                spent = getattr(b, 'spent', getattr(b, 'spent_amount', 0.0)) or 0.0
                limit = b.amount or 1.0
                cat_name = b.category.name if hasattr(b, 'category') and b.category else "General"
                
                if spent >= limit:
                    title = f"Budget Exceeded: {cat_name}"
                    if not is_duplicate("budget", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"You have spent ₹{spent:,.2f} exceeding your ₹{limit:,.2f} limit for {cat_name}.",
                            category="budget",
                            priority="critical",
                            icon="AlertCircle",
                            action_url="/dashboard/budgets"
                        )
                        db.add(notif)
                        created_notifications.append(notif)
                elif spent >= 0.8 * limit:
                    pct = round((spent / limit) * 100)
                    title = f"Budget Nearing Limit: {cat_name}"
                    if not is_duplicate("budget", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"You have used {pct}% of your ₹{limit:,.2f} budget for {cat_name}.",
                            category="budget",
                            priority="high",
                            icon="Sliders",
                            action_url="/dashboard/budgets"
                        )
                        db.add(notif)
                        created_notifications.append(notif)

        # 2. Bill Reminders
        if prefs.enable_bill_reminders:
            bills = db.query(Bill).filter(Bill.user_id == user_id).all()
            unpaid_bills = [b for b in bills if not getattr(b, 'is_paid', getattr(b, 'status', '') == 'paid')]
            for bill in unpaid_bills:
                due_d = bill.due_date.date() if isinstance(bill.due_date, datetime) else bill.due_date
                b_name = getattr(bill, 'name', getattr(bill, 'title', 'Bill'))
                b_amt = bill.amount or 0.0

                if due_d < now_date:
                    title = f"Overdue Bill: {b_name}"
                    if not is_duplicate("bills", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"Overdue payment of ₹{b_amt:,.2f} for {b_name} was due on {due_d.strftime('%b %d')}.",
                            category="bills",
                            priority="critical",
                            icon="Clock",
                            action_url="/dashboard/bills"
                        )
                        db.add(notif)
                        created_notifications.append(notif)
                elif due_d == now_date:
                    title = f"Bill Due Today: {b_name}"
                    if not is_duplicate("bills", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"Payment of ₹{b_amt:,.2f} for {b_name} is due today!",
                            category="bills",
                            priority="critical",
                            icon="Calendar",
                            action_url="/dashboard/bills"
                        )
                        db.add(notif)
                        created_notifications.append(notif)
                elif due_d <= now_date + timedelta(days=3):
                    title = f"Upcoming Bill: {b_name}"
                    if not is_duplicate("bills", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"Payment of ₹{b_amt:,.2f} for {b_name} is due on {due_d.strftime('%b %d')}.",
                            category="bills",
                            priority="high",
                            icon="Calendar",
                            action_url="/dashboard/bills"
                        )
                        db.add(notif)
                        created_notifications.append(notif)

        # 3. Goal Updates & Achievements
        if prefs.enable_goal_updates or prefs.enable_achievements:
            goals = db.query(Goal).filter(Goal.user_id == user_id).all()
            for g in goals:
                curr = g.current_amount or 0.0
                target = g.target_amount or 1.0
                g_title = getattr(g, 'name', getattr(g, 'title', 'Savings Goal'))

                if curr >= target and prefs.enable_achievements:
                    title = f"Goal Completed: {g_title}! 🎉"
                    if not is_duplicate("achievements", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"Congratulations! You reached your ₹{target:,.2f} target for {g_title}.",
                            category="achievements",
                            priority="high",
                            icon="Target",
                            action_url="/dashboard/goals"
                        )
                        db.add(notif)
                        created_notifications.append(notif)
                elif curr >= 0.5 * target and prefs.enable_goal_updates:
                    pct = round((curr / target) * 100)
                    title = f"Goal Milestone: {g_title}"
                    if not is_duplicate("goals", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"You crossed {pct}% of your target for {g_title} (₹{curr:,.2f} saved).",
                            category="goals",
                            priority="medium",
                            icon="Target",
                            action_url="/dashboard/goals"
                        )
                        db.add(notif)
                        created_notifications.append(notif)

        # 4. Forecast Warnings
        if prefs.enable_forecast_warnings:
            try:
                fc = CashFlowForecastService().generate_forecast(db, user_id=user_id, period="30d", include_ai_explanation=False)
                proj_bal = fc.get("projected_end_balance", 0.0)
                if proj_bal < 0:
                    title = "Predictive Cashflow Deficit Risk"
                    if not is_duplicate("forecast", title):
                        notif = Notification(
                            user_id=user_id,
                            title=title,
                            message=f"30-day forecast predicts a negative balance (₹{proj_bal:,.2f}). Review discretionary budgets.",
                            category="forecast",
                            priority="critical",
                            icon="TrendingDown",
                            action_url="/dashboard/forecast"
                        )
                        db.add(notif)
                        created_notifications.append(notif)
            except Exception as e:
                logger.warning("Notification generator forecast check skipped: %s", str(e))

        # 5. AI Financial Briefing Recommendation
        if prefs.enable_ai_recommendations:
            summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period="30d")
            health_score = summary.get("health_score", 88)
            title = "AI Financial Health Update"
            if not is_duplicate("ai", title):
                notif = Notification(
                    user_id=user_id,
                    title=title,
                    message=f"Your Financial Health Score is {health_score}/100. AI Personal CFO coaching analysis ready.",
                    category="ai",
                    priority="medium",
                    icon="Sparkles",
                    action_url="/dashboard/chat"
                )
                db.add(notif)
                created_notifications.append(notif)

        if created_notifications:
            db.commit()

        return created_notifications


class NotificationService:
    @classmethod
    def list_notifications(
        cls,
        db: Session,
        user_id: int,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        unread_only: bool = False,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lists notifications with rich filtering, search, pagination, and unread counts.
        Also automatically triggers smart notification generation.
        """
        # Generate any fresh notifications
        try:
            NotificationGenerator.generate_smart_notifications(db, user_id)
        except Exception as exc:
            logger.warning("Smart notification generation warning: %s", str(exc))

        query = db.query(Notification).filter(Notification.user_id == user_id)

        if category and category != "all":
            query = query.filter(Notification.category == category)
        if priority and priority != "all":
            query = query.filter(Notification.priority == priority)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Notification.title.ilike(search_pattern),
                    Notification.message.ilike(search_pattern)
                )
            )

        total_count = query.count()
        items = query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()

        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

        critical_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.priority == "critical"
        ).count()

        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "critical_count": critical_count,
            "items": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "category": n.category,
                    "priority": n.priority,
                    "icon": n.icon,
                    "is_read": n.is_read,
                    "action_url": n.action_url,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                    "expires_at": n.expires_at.isoformat() if n.expires_at else None
                }
                for n in items
            ]
        }

    @classmethod
    def mark_as_read(cls, db: Session, user_id: int, notification_id: int) -> Optional[Notification]:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            notif.updated_at = datetime.now()
            db.commit()
            db.refresh(notif)
        return notif

    @classmethod
    def mark_all_as_read(cls, db: Session, user_id: int) -> int:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True, "updated_at": datetime.now()})
        db.commit()
        return count

    @classmethod
    def delete_notification(cls, db: Session, user_id: int, notification_id: int) -> bool:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            db.delete(notif)
            db.commit()
            return True
        return False
