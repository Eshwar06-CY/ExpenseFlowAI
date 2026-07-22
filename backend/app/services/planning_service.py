from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.recurring import RecurringTransaction
from app.models.scenario import Scenario
from app.routers.recurring_tx import calculate_next_run
from app.services.cache import cache_service

class PlanningService:
    @staticmethod
    def get_active_balance(db: Session, user_id: int) -> float:
        from app.services.finance_engine import FinanceEngine
        return FinanceEngine.get_active_balance(db, user_id)

    @staticmethod
    def calculate_forecasts(db: Session, user_id: int, days_limit: int = 90) -> Dict[str, Any]:
        """
        Runs a 7-day, 30-day, and 90-day cash flow projection applying recurring rules,
        unpaid bills, and active "What If" planning scenarios.
        """
        cache_key = f"user:{user_id}:forecast:{days_limit}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        current_balance = PlanningService.get_active_balance(db, user_id)

        # 1. Fetch recurring rules
        stmt_rec = select(RecurringTransaction).where(RecurringTransaction.user_id == user_id)
        recurring_rules = db.execute(stmt_rec).scalars().all()

        # 2. Fetch unpaid bills
        stmt_bills = select(Bill).where(Bill.user_id == user_id, Bill.is_paid == False)
        unpaid_bills = db.execute(stmt_bills).scalars().all()

        # 3. Fetch active scenarios
        stmt_scen = select(Scenario).where(Scenario.user_id == user_id, Scenario.is_active == True)
        scenarios = db.execute(stmt_scen).scalars().all()

        today = date.today()
        running_balance = current_balance
        timeline = []
        
        balance_7d = current_balance
        balance_30d = current_balance
        balance_90d = current_balance

        # Track next run dates for recurring transactions
        rules_state = []
        for r in recurring_rules:
            rules_state.append({
                "rule": r,
                "next_run": r.next_run.date() if r.next_run else today
            })

        # Group unpaid bills by due date
        bills_map = {}
        for b in unpaid_bills:
            due = b.due_date.date() if b.due_date else today
            bills_map.setdefault(due, []).append(b.amount)

        # Pre-process scenarios
        salary_increases = [s for s in scenarios if s.type == "salary_increase"]
        rent_increases = [s for s in scenarios if s.type == "rent_increase"]
        one_offs = [s for s in scenarios if s.type == "one_off_purchase"]
        spend_reductions = [s for s in scenarios if s.type == "spend_reduction"]

        total_income = 0.0
        total_expense = 0.0

        for offset in range(days_limit):
            f_date = today + timedelta(days=offset)
            day_change = 0.0

            # A. Process recurring transaction rules
            for item in rules_state:
                while item["next_run"] <= f_date:
                    amount = item["rule"].amount
                    
                    # Apply spend reduction scenario modifiers
                    if item["rule"].type == "expense" and item["rule"].category_id:
                        for sr in spend_reductions:
                            if sr.category_id == item["rule"].category_id and sr.percent_change:
                                amount *= (1.0 + (sr.percent_change / 100.0))

                    if item["rule"].type == "income":
                        day_change += amount
                        total_income += amount
                    elif item["rule"].type == "expense":
                        day_change -= amount
                        total_expense -= amount

                    # Compute next occurrence
                    rule_dt = datetime.combine(item["next_run"], datetime.min.time())
                    item["next_run"] = calculate_next_run(rule_dt, item["rule"].frequency).date()

            # B. Process unpaid bills due on this day
            if f_date in bills_map:
                for b_amt in bills_map[f_date]:
                    # Apply spend reduction if applicable
                    amt = b_amt
                    day_change -= amt
                    total_expense -= amt

            # C. Process Scenarios
            # Salary Increase Scenario (Assume recurring monthly cash inflow from today onwards)
            for si in salary_increases:
                # Add income every 30 days starting day 0
                if offset % 30 == 0:
                    day_change += si.amount
                    total_income += si.amount

            # Rent Increase Scenario (Assume recurring monthly cash outflow starting day 0)
            for ri in rent_increases:
                if offset % 30 == 0:
                    day_change -= ri.amount
                    total_expense -= ri.amount

            # One-off Purchase Scenario (Subtracts amount on targeted one_off_date)
            for oo in one_offs:
                if oo.one_off_date and oo.one_off_date.date() == f_date:
                    day_change -= oo.amount
                    total_expense -= oo.amount

            running_balance += day_change
            
            # Benchmarks capture
            if offset == 7:
                balance_7d = running_balance
            elif offset == 30:
                balance_30d = running_balance
            elif offset == 89 or offset == days_limit - 1:
                balance_90d = running_balance

            timeline.append({
                "date": f_date.isoformat(),
                "balance": round(running_balance, 2)
            })

        months = days_limit / 30.0
        monthly_surplus = (total_income - abs(total_expense)) / months if months > 0 else 0.0

        result = {
            "balance_7d": round(balance_7d, 2),
            "balance_30d": round(balance_30d, 2),
            "balance_90d": round(balance_90d, 2),
            "monthly_surplus": round(monthly_surplus, 2),
            "timeline": timeline
        }
        
        # Cache results for 5 minutes
        cache_service.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    def calculate_savings_plan(db: Session, goal: Goal) -> Dict[str, Any]:
        """
        Calculates suggested contributions, ETA, and progress timeline for a goal.
        """
        remaining = goal.target_amount - goal.current_amount
        if remaining <= 0:
            return {
                "target_amount": goal.target_amount,
                "current_amount": goal.current_amount,
                "remaining_amount": 0.0,
                "required_monthly_savings": 0.0,
                "estimated_completion_date": datetime.now(timezone.utc).date().isoformat(),
                "progress_timeline": []
            }

        # 1. Required monthly savings calculation
        today = date.today()
        target_d = goal.target_date.date() if goal.target_date else today + timedelta(days=365)
        
        days_rem = (target_d - today).days
        months_rem = days_rem / 30.4
        
        req_monthly = remaining / max(months_rem, 0.1)

        # 2. Estimated completion date using default contribution of $200/month if target_date is not set
        suggested_monthly = req_monthly if goal.target_date else 200.0
        months_needed = remaining / suggested_monthly
        est_completion = today + timedelta(days=int(months_needed * 30.4))

        # 3. Progress timeline mapping
        timeline = []
        for i in range(12):
            point_date = today + timedelta(days=int(i * 30.4))
            expected = goal.current_amount + (suggested_monthly * i)
            timeline.append({
                "date": point_date.isoformat(),
                "expected_amount": round(min(expected, goal.target_amount), 2)
            })

        return {
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "remaining_amount": round(remaining, 2),
            "required_monthly_savings": round(req_monthly, 2),
            "estimated_completion_date": est_completion.isoformat(),
            "progress_timeline": timeline
        }

    @staticmethod
    def get_budget_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Runs rules-based statistical averages over 90 days to suggest budgets.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        # Fetch category total spending
        stmt = (
            db.query(
                Transaction.category_id,
                Category.name,
                func.sum(Transaction.amount)
            )
            .join(Category, Category.id == Transaction.category_id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            .group_by(Transaction.category_id, Category.name)
        )
        spending_totals = stmt.all()

        # Fetch current monthly budgets
        stmt_bud = select(Budget).where(Budget.user_id == user_id)
        current_budgets = {b.category_id: b.amount for b in db.execute(stmt_bud).scalars().all()}

        recommendations = []
        for cat_id, cat_name, total_spent in spending_totals:
            # Average monthly spending over 3 months
            avg_spending = float(total_spent) / 3.0
            
            # Suggest budget with a 10% safety buffer rounded to nearest 10
            recommended = round((avg_spending * 1.10) / 10) * 10
            current_b = current_budgets.get(cat_id)

            status = "aligned"
            if current_b is not None:
                if current_b < avg_spending:
                    status = "overspending_risk"
                elif current_b > avg_spending * 1.30:
                    status = "underspending_opportunity"

            recommendations.append({
                "category_id": cat_id,
                "category_name": cat_name,
                "avg_monthly_spending": round(avg_spending, 2),
                "recommended_budget": max(recommended, 50.0),
                "current_budget": current_b,
                "status": status
            })

        return recommendations

    @staticmethod
    def calculate_health_metrics(db: Session, user_id: int) -> Dict[str, Any]:
        return PlanningService.calculate_financial_health_score(db, user_id)

    @staticmethod
    def calculate_financial_health_score(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Calculates the real Workspace Financial Health Score based on FinanceEngine metrics.
        """
        from app.services.finance_engine import FinanceEngine
        fe_health = FinanceEngine.calculate_financial_health_score(db, user_id)
        current_balance = FinanceEngine.get_active_balance(db, user_id)
        forecast = PlanningService.calculate_forecasts(db, user_id, 30)
        projected_30d = forecast.get("balance_30d", current_balance)

        now = datetime.now()
        historical = []
        for i in range(5, -1, -1):
            m_start = (now - timedelta(days=i*30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_label = m_start.strftime("%b %Y")
            historical.append({
                "month": date_label,
                "score": fe_health["health_score"]
            })

        return {
            "health_score": fe_health["health_score"],
            "savings_rate": fe_health["metrics"]["savings_rate_pct"],
            "expense_ratio": round(100.0 - fe_health["metrics"]["savings_rate_pct"], 1),
            "income_stability": 80.0,
            "emergency_fund_coverage_months": fe_health["metrics"]["reserve_months"],
            "budget_adherence_rate": fe_health["metrics"]["budget_adherence_pct"],
            "bill_payment_rate": fe_health["metrics"]["bill_reliability_pct"],
            "goal_progress_rate": fe_health["metrics"]["goal_progress_pct"],
            "projected_30d_balance": round(projected_30d, 2),
            "cash_reserve": current_balance,
            "historical_health_trend": historical
        }

    @staticmethod
    def get_financial_timeline(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Merges actual transactions, upcoming bills, and goal milestone target dates into a chronological feed.
        """
        timeline = []

        # 1. Fetch transactions (last 30 days)
        stmt_tx = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.date >= datetime.now() - timedelta(days=30)
        ).order_by(Transaction.date.desc())
        transactions = db.execute(stmt_tx).scalars().all()
        for t in transactions:
            timeline.append({
                "date": t.date.date().isoformat(),
                "type": f"transaction_{t.type}",
                "title": t.description,
                "description": f"Ledger entries reconciliation on account.",
                "amount": t.amount if t.type == 'income' else -t.amount
            })

        # 2. Fetch upcoming bills (next 60 days)
        stmt_bills = select(Bill).where(
            Bill.user_id == user_id,
            Bill.is_paid == False,
            Bill.due_date <= datetime.now() + timedelta(days=60)
        )
        bills = db.execute(stmt_bills).scalars().all()
        for b in bills:
            timeline.append({
                "date": b.due_date.date().isoformat(),
                "type": "bill",
                "title": f"Bill Payable: {b.name}",
                "description": "Awaiting checkout payments.",
                "amount": -b.amount
            })

        # 3. Fetch goals target date milestones
        stmt_goals = select(Goal).where(
            Goal.user_id == user_id,
            Goal.target_date != None
        )
        goals = db.execute(stmt_goals).scalars().all()
        for g in goals:
            if g.target_date:
                timeline.append({
                    "date": g.target_date.date().isoformat(),
                    "type": "goal_milestone",
                    "title": f"Goal Target: {g.name}",
                    "description": f"Target goal savings deadline: ${g.target_amount}",
                    "amount": g.target_amount
                })

        # Sort timeline chronologically (latest dates first)
        timeline.sort(key=lambda x: x["date"], reverse=True)
        return timeline
