from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.budget import Budget
from app.models.bill import Bill
from app.models.recurring import RecurringTransaction
from app.models.insight import FinancialInsight, FinancialEvent, DailyBriefing
from app.models.category import Category
from app.routers.recurring_tx import calculate_next_run

class InsightsEngine:
    """
    InsightsEngine calculates spending trends, recurring patterns,
    cash flow forecasts, financial health scores, and structured briefings.
    """
    
    @staticmethod
    def generate_insights(db: Session, user_id: int) -> List[FinancialInsight]:
        # Delete old insights to ensure clean reload
        db.execute(delete(FinancialInsight).where(FinancialInsight.user_id == user_id))
        db.commit()
        db.expire_all()

        generated_insights = []

        # 1. Fetch all expenses
        stmt_expenses = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.user_id == user_id, Transaction.type == "expense")
            .order_by(Transaction.date.asc())
        )
        expenses = db.execute(stmt_expenses).scalars().all()

        # Calculate Spending Trends across categories
        category_totals: Dict[str, float] = {}
        for tx in expenses:
            cat_name = tx.category.name if tx.category else "Uncategorized"
            category_totals[cat_name] = category_totals.get(cat_name, 0.0) + tx.amount

        if category_totals:
            insight_cats = FinancialInsight(
                user_id=user_id,
                type="trend",
                title="Category Spending Distribution",
                description="Analysis of your historical outflows grouped by category.",
                data={"category_breakdown": category_totals}
            )
            generated_insights.append(insight_cats)

        # Detect Recurring Patterns (e.g. count >= 3 with roughly uniform intervals)
        description_groups: Dict[str, List[datetime]] = {}
        for tx in expenses:
            desc = tx.description.strip().lower()
            if len(desc) >= 3:
                description_groups.setdefault(tx.description, []).append(tx.date)

        detected_recurring = []
        for desc, dates in description_groups.items():
            if len(dates) >= 3:
                # Calculate diffs
                dates_sorted = sorted(dates)
                diffs = []
                for i in range(len(dates_sorted) - 1):
                    diffs.append((dates_sorted[i+1] - dates_sorted[i]).days)
                
                avg_diff = sum(diffs) / len(diffs)
                # Check standard weekly (~7 days) or monthly (~30 days) deviation
                is_recurring = False
                freq_detected = ""
                if 5 <= avg_diff <= 9:
                    is_recurring = True
                    freq_detected = "weekly"
                elif 25 <= avg_diff <= 35:
                    is_recurring = True
                    freq_detected = "monthly"

                if is_recurring:
                    detected_recurring.append({
                        "name": desc,
                        "frequency": freq_detected,
                        "average_interval_days": round(avg_diff, 1),
                        "frequency_count": len(dates)
                    })

        if detected_recurring:
            insight_patterns = FinancialInsight(
                user_id=user_id,
                type="pattern",
                title="Detected Subscriptions & Recurring Patterns",
                description="Identified repeating outflows which could represent active subscriptions.",
                data={"recurring_patterns": detected_recurring}
            )
            generated_insights.append(insight_patterns)

        # Calculate Cash Flow Forecast & Health Metrics before adding new objects to avoid auto-flush warnings
        forecast_data = InsightsEngine.calculate_forecasts(db, user_id)
        health_metrics = InsightsEngine.calculate_health_metrics(db, user_id)

        if forecast_data:
            insight_forecast = FinancialInsight(
                user_id=user_id,
                type="forecast",
                title="30-Day Liquidity Forecast",
                description="Projected net balance flow across the next 30 days based on active recurring schedules.",
                data={"forecast": forecast_data}
            )
            generated_insights.append(insight_forecast)

        insight_health = FinancialInsight(
            user_id=user_id,
            type="health",
            title="Financial Health Metrics",
            description="Reconciled health indicators like savings rate and cash burn rate.",
            data=health_metrics
        )
        generated_insights.append(insight_health)

        db.add_all(generated_insights)
        db.commit()
        # Refresh for return responses
        for ins in generated_insights:
            db.refresh(ins)
        return generated_insights

    @staticmethod
    def calculate_health_metrics(db: Session, user_id: int) -> Dict[str, Any]:
        from app.services.finance_engine import FinanceEngine
        now = datetime.now()
        start_month = datetime(now.year, now.month, 1)
        totals = FinanceEngine.get_period_totals(db, user_id, start_date=start_month)
        reserve = FinanceEngine.get_cash_reserve_metrics(db, user_id)
        budget = FinanceEngine.get_budget_adherence(db, user_id)
        balance = FinanceEngine.get_active_balance(db, user_id)

        return {
            "total_balance": balance,
            "monthly_income": totals["income"],
            "monthly_expenses": totals["expense"],
            "savings_rate": totals["savings_rate"],
            "burn_rate_months": reserve["reserve_months"],
            "budget_adherence_rate": budget["adherence_rate_pct"]
        }

    @staticmethod
    def calculate_forecasts(db: Session, user_id: int) -> List[Dict[str, Any]]:
        # Fetch current balance
        stmt_bal = select(func.sum(Account.balance)).where(Account.user_id == user_id)
        current_balance = db.execute(stmt_bal).scalar() or 0.0

        # Fetch recurring transactions
        stmt_rec = select(RecurringTransaction).where(RecurringTransaction.user_id == user_id)
        recurring_rules = db.execute(stmt_rec).scalars().all()

        projected = []
        today = date.today()
        running_balance = current_balance

        # Active projections index map
        projected_rules = []
        for r in recurring_rules:
            projected_rules.append({
                "rule": r,
                "projected_next": r.next_run.date()
            })

        for day_offset in range(30):
            forecast_date = today + timedelta(days=day_offset)
            
            # Apply scheduled transactions falling on forecast_date
            day_change = 0.0
            for item in projected_rules:
                while item["projected_next"] <= forecast_date:
                    # Apply
                    if item["rule"].type == "income":
                        day_change += item["rule"].amount
                    elif item["rule"].type == "expense":
                        day_change -= item["rule"].amount
                    
                    # Compute next projected run date
                    rule_next_dt = datetime.combine(item["projected_next"], datetime.min.time())
                    next_run_dt = calculate_next_run(rule_next_dt, item["rule"].frequency)
                    item["projected_next"] = next_run_dt.date()

            running_balance += day_change
            projected.append({
                "date": forecast_date.isoformat(),
                "balance": round(running_balance, 2)
            })

        return projected

    @staticmethod
    def detect_events(db: Session, user_id: int) -> List[FinancialEvent]:
        # Delete old events to ensure reload
        db.execute(delete(FinancialEvent).where(FinancialEvent.user_id == user_id))
        db.commit()

        events = []
        now_dt = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Detect large transactions (expense >= 500)
        stmt_large = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.amount >= 500.0
        )
        large_txs = db.execute(stmt_large).scalars().all()
        for tx in large_txs:
            evt = FinancialEvent(
                user_id=user_id,
                event_type="large_expense",
                title=f"Large Transaction Detected: {tx.description}",
                description=f"An expense of ${tx.amount:,.2f} was recorded on {tx.date.strftime('%Y-%m-%d')}.",
                severity="medium",
                event_date=tx.date
            )
            db.add(evt)
            events.append(evt)

        # 2. Detect budget warnings (spent >= 90% of limit)
        stmt_budgets = select(Budget).options(joinedload(Budget.category)).where(Budget.user_id == user_id)
        budgets = db.execute(stmt_budgets).scalars().all()
        for b in budgets:
            ratio = (b.spent / b.amount) * 100 if b.amount > 0 else 0
            if ratio >= 90.0:
                cat_name = b.category.name if b.category else "Category"
                evt = FinancialEvent(
                    user_id=user_id,
                    event_type="budget_warning",
                    title=f"Budget warning: {cat_name}",
                    description=f"You have utilized {ratio:.1f}% of your ${b.amount:,.2f} budget for {cat_name}.",
                    severity="high" if ratio > 100 else "medium",
                    event_date=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                db.add(evt)
                events.append(evt)

        # 3. Detect upcoming bills (due in next 3 days)
        limit_date = now_dt + timedelta(days=3)
        stmt_bills = select(Bill).where(
            Bill.user_id == user_id,
            Bill.is_paid == False,
            Bill.due_date <= limit_date
        )
        upcoming_bills = db.execute(stmt_bills).scalars().all()
        for bill in upcoming_bills:
            is_overdue = bill.due_date < now_dt
            evt = FinancialEvent(
                user_id=user_id,
                event_type="upcoming_bill",
                title=f"Bill {'Overdue' if is_overdue else 'Due Soon'}: {bill.name}",
                description=f"Payment of ${bill.amount:,.2f} is due by {bill.due_date.strftime('%Y-%m-%d')}.",
                severity="high" if is_overdue else "medium",
                event_date=bill.due_date
            )
            db.add(evt)
            events.append(evt)

        db.commit()
        for evt in events:
            db.refresh(evt)
        return events

    @staticmethod
    def generate_daily_briefing(db: Session, user_id: int) -> DailyBriefing:
        today_date = date.today()
        
        # 1. Regenerate insights & events to ensure briefing contains up to date calculations
        InsightsEngine.generate_insights(db, user_id)
        events = InsightsEngine.detect_events(db, user_id)
        
        # Calculate health metrics
        health = InsightsEngine.calculate_health_metrics(db, user_id)
        
        # Calculate cash flow forecast endpoints
        forecast = InsightsEngine.calculate_forecasts(db, user_id)
        projected_30d_balance = forecast[-1]["balance"] if forecast else health["total_balance"]
        
        # Collect unread active warnings
        active_warnings = []
        for e in events:
            if not e.is_dismissed:
                active_warnings.append({
                    "id": e.id,
                    "event_type": e.event_type,
                    "title": e.title,
                    "description": e.description,
                    "severity": e.severity
                })

        briefing_content = {
            "health_score": round((health["savings_rate"] + health["budget_adherence_rate"]) / 2.0 if health["savings_rate"] > 0 else health["budget_adherence_rate"] / 2.0),
            "total_balance": health["total_balance"],
            "projected_balance_30d": projected_30d_balance,
            "savings_rate": health["savings_rate"],
            "burn_rate_months": health["burn_rate_months"],
            "warnings_count": len(active_warnings),
            "warnings": active_warnings
        }

        # Check if briefing for today already exists, if so upsert it
        stmt_brief = select(DailyBriefing).where(DailyBriefing.user_id == user_id, DailyBriefing.date == today_date)
        briefing = db.execute(stmt_brief).scalar_one_or_none()
        if briefing:
            briefing.content = briefing_content
            briefing.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            briefing = DailyBriefing(
                user_id=user_id,
                date=today_date,
                content=briefing_content
            )
            db.add(briefing)

        db.commit()
        db.refresh(briefing)
        return briefing
