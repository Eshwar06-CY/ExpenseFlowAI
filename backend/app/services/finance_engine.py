"""
FinanceEngine Service - ExpenseFlowAI

Centralized single source of truth for all financial metrics, health scoring,
period totals, category spending breakdowns, cash flow trends, budget adherence,
and liquidity forecasting across ExpenseFlowAI.
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.category import Category
from app.services.cache import cache_service


class FinanceEngine:
    @staticmethod
    def get_active_balance(db: Session, user_id: int) -> float:
        """
        Calculates total available liquid balance across all active accounts.
        Returns 0.0 if user has no accounts configured.
        """
        stmt = select(func.sum(Account.balance)).where(
            Account.user_id == user_id
        )
        val = db.execute(stmt).scalar()
        return round(float(val), 2) if val is not None else 0.0

    @staticmethod
    def get_period_totals(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculates total income, total expenses, net savings, and savings rate percentage
        for a given user within an optional date range.
        Handles division-by-zero safely if total income is 0.
        """
        stmt_inc = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "income"
        )
        stmt_exp = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        )

        if start_date:
            stmt_inc = stmt_inc.where(Transaction.date >= start_date)
            stmt_exp = stmt_exp.where(Transaction.date >= start_date)
        if end_date:
            stmt_inc = stmt_inc.where(Transaction.date <= end_date)
            stmt_exp = stmt_exp.where(Transaction.date <= end_date)

        total_income = float(db.execute(stmt_inc).scalar() or 0.0)
        total_expenses = float(db.execute(stmt_exp).scalar() or 0.0)
        net_savings = total_income - total_expenses

        # Division by zero protection
        savings_rate = ((net_savings / total_income) * 100.0) if total_income > 0 else 0.0

        return {
            "income": round(total_income, 2),
            "expense": round(total_expenses, 2),
            "net_savings": round(net_savings, 2),
            "savings_rate": round(savings_rate, 2),
        }

    @staticmethod
    def get_category_spending(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Groups expense transactions by category, calculating total amount spent and percentage.
        """
        query = (
            db.query(
                Transaction.category_id,
                Category.name.label("category_name"),
                Category.color.label("category_color"),
                func.sum(Transaction.amount).label("amount")
            )
            .outerjoin(Category, Category.id == Transaction.category_id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense"
            )
        )

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        results = query.group_by(Transaction.category_id, Category.name, Category.color).all()
        
        total_spent = sum(r.amount for r in results) if results else 0.0
        
        categories = []
        for r in results:
            cat_name = r.category_name or "Uncategorized"
            amount = float(r.amount or 0.0)
            percentage = (amount / total_spent * 100.0) if total_spent > 0 else 0.0
            categories.append({
                "category_id": r.category_id,
                "category": cat_name,
                "amount": round(amount, 2),
                "percentage": round(percentage, 2),
                "color": r.category_color or "#9f6ff5"
            })
            
        categories.sort(key=lambda x: x["amount"], reverse=True)
        return categories

    @staticmethod
    def get_monthly_trends(db: Session, user_id: int, months_count: int = 6) -> List[Dict[str, Any]]:
        """
        Computes historical cash flow trends grouped by calendar month over the specified window.
        """
        now = datetime.now()
        trends = []

        for i in range(months_count - 1, -1, -1):
            # Compute month bounds
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1

            m_start = datetime(year, month, 1)
            if month == 12:
                m_end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
            else:
                m_end = datetime(year, month + 1, 1) - timedelta(microseconds=1)

            month_label = m_start.strftime("%b %Y")

            totals = FinanceEngine.get_period_totals(db, user_id, start_date=m_start, end_date=m_end)
            trends.append({
                "month": month_label,
                "year": year,
                "month_num": month,
                "income": totals["income"],
                "expenses": totals["expense"],
                "net": totals["net_savings"]
            })

        return trends

    @staticmethod
    def get_budget_adherence(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Evaluates active budgets and calculates spending limit adherence rate.
        """
        stmt = select(Budget).where(Budget.user_id == user_id)
        budgets = db.execute(stmt).scalars().all()

        if not budgets:
            return {
                "total_budgets": 0,
                "exceeded_budgets": 0,
                "adherence_rate_pct": 100.0,
                "budgets": []
            }

        exceeded = 0
        budget_details = []

        for b in budgets:
            ratio = (b.spent / b.amount * 100.0) if b.amount > 0 else 0.0
            is_exceeded = b.spent > b.amount
            if is_exceeded:
                exceeded += 1

            budget_details.append({
                "id": b.id,
                "category_id": b.category_id,
                "category_name": b.category.name if b.category else "General",
                "amount": float(b.amount),
                "spent": float(b.spent),
                "remaining": round(float(b.amount - b.spent), 2),
                "ratio_pct": round(ratio, 2),
                "is_exceeded": is_exceeded
            })

        adherence_rate = ((len(budgets) - exceeded) / len(budgets)) * 100.0

        return {
            "total_budgets": len(budgets),
            "exceeded_budgets": exceeded,
            "adherence_rate_pct": round(adherence_rate, 2),
            "budgets": budget_details
        }

    @staticmethod
    def get_bill_reliability(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Evaluates bill payments and calculates payment reliability rate and pending dues.
        """
        stmt = select(Bill).where(Bill.user_id == user_id)
        bills = db.execute(stmt).scalars().all()

        if not bills:
            return {
                "total_bills": 0,
                "paid_bills": 0,
                "unpaid_bills": 0,
                "unpaid_dues_sum": 0.0,
                "reliability_rate_pct": 100.0
            }

        paid_count = sum(1 for b in bills if b.is_paid)
        unpaid_count = len(bills) - paid_count
        unpaid_sum = sum(b.amount for b in bills if not b.is_paid)

        reliability_rate = (paid_count / len(bills)) * 100.0

        return {
            "total_bills": len(bills),
            "paid_bills": paid_count,
            "unpaid_bills": unpaid_count,
            "unpaid_dues_sum": round(float(unpaid_sum), 2),
            "reliability_rate_pct": round(reliability_rate, 2)
        }

    @staticmethod
    def get_cash_reserve_metrics(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Calculates liquid balance, monthly burn rate, and emergency cash reserve months.
        """
        current_balance = FinanceEngine.get_active_balance(db, user_id)
        
        # 30-day expenses
        now = datetime.now()
        start_30d = now - timedelta(days=30)
        totals_30d = FinanceEngine.get_period_totals(db, user_id, start_date=start_30d)
        
        monthly_expense = totals_30d["expense"]
        
        # If no recent monthly expenses, use default 1.0 to avoid division by zero
        denom = max(monthly_expense, 1.0)
        reserve_months = current_balance / denom

        return {
            "total_balance": current_balance,
            "monthly_expense_30d": monthly_expense,
            "reserve_months": round(float(reserve_months), 1)
        }

    @staticmethod
    def calculate_financial_health_score(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Calculates the standardized Workspace Financial Health Score (0-100 scale)
        based on 5 weighted financial pillars:
        1. Savings Rate (25%)
        2. Cash Reserve Safety (25%)
        3. Budget Adherence (20%)
        4. Bill Payment Reliability (15%)
        5. Goal Progress Velocity (15%)
        """
        cache_key = f"user:{user_id}:health_score"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        # 1. 30-Day Savings Rate (25% weight)
        now = datetime.now()
        start_30d = now - timedelta(days=30)
        totals_30d = FinanceEngine.get_period_totals(db, user_id, start_date=start_30d)
        savings_rate = totals_30d["savings_rate"]
        score_savings = min(25.0, (max(savings_rate, 0.0) / 30.0) * 25.0)

        # 2. Cash Reserve Safety (25% weight)
        reserve_data = FinanceEngine.get_cash_reserve_metrics(db, user_id)
        reserve_months = reserve_data["reserve_months"]
        score_reserve = min(25.0, (max(reserve_months, 0.0) / 3.0) * 25.0)

        # 3. Budget Adherence (20% weight)
        budget_data = FinanceEngine.get_budget_adherence(db, user_id)
        adherence_pct = budget_data["adherence_rate_pct"]
        score_budget = (adherence_pct / 100.0) * 20.0

        # 4. Bill Reliability (15% weight)
        bill_data = FinanceEngine.get_bill_reliability(db, user_id)
        bill_pct = bill_data["reliability_rate_pct"]
        score_bill = (bill_pct / 100.0) * 15.0

        # 5. Goal Progress Velocity (15% weight)
        stmt_goals = select(Goal).where(Goal.user_id == user_id)
        goals = db.execute(stmt_goals).scalars().all()
        if goals:
            pcts = [min((g.current_amount / max(g.target_amount, 1.0)) * 100.0, 100.0) for g in goals]
            avg_goal_pct = sum(pcts) / len(goals)
        else:
            avg_goal_pct = 100.0
        score_goal = (avg_goal_pct / 100.0) * 15.0

        # Sum and clamp to 0-100
        raw_score = score_savings + score_reserve + score_budget + score_bill + score_goal
        final_score = int(round(min(100.0, max(0.0, raw_score))))

        status = "Excellent" if final_score >= 80 else ("Healthy" if final_score >= 50 else "Critical")

        result = {
            "health_score": final_score,
            "status": status,
            "metrics": {
                "savings_rate_pct": savings_rate,
                "reserve_months": reserve_months,
                "budget_adherence_pct": adherence_pct,
                "bill_reliability_pct": bill_pct,
                "goal_progress_pct": round(avg_goal_pct, 2)
            },
            "components": {
                "savings_score": round(score_savings, 1),
                "reserve_score": round(score_reserve, 1),
                "budget_score": round(score_budget, 1),
                "bill_score": round(score_bill, 1),
                "goal_score": round(score_goal, 1)
            }
        }

        cache_service.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    def get_dashboard_summary(db: Session, user_id: int, period: str = "30d") -> Dict[str, Any]:
        """
        Returns a complete, consolidated dashboard summary object computed from DB records.
        """
        # Parse period
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period.lower(), 30)

        now = datetime.now()
        start_period = now - timedelta(days=days)

        # 1. Available liquid balance
        total_balance = FinanceEngine.get_active_balance(db, user_id)

        # 2. Period totals
        period_totals = FinanceEngine.get_period_totals(db, user_id, start_date=start_period)

        # 3. All-time totals for stats fallback
        all_time_totals = FinanceEngine.get_period_totals(db, user_id)

        # 4. Category spending
        category_spending = FinanceEngine.get_category_spending(db, user_id, start_date=start_period)

        # 5. Monthly trends
        monthly_trends = FinanceEngine.get_monthly_trends(db, user_id, months_count=6)

        # 6. Health score
        health_data = FinanceEngine.calculate_financial_health_score(db, user_id)

        # 7. Recent transactions
        stmt_tx = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(5)
        )
        recent_txs = db.execute(stmt_tx).scalars().all()

        recent_formatted = []
        for t in recent_txs:
            recent_formatted.append({
                "id": t.id,
                "amount": float(t.amount),
                "type": t.type,
                "category": t.category.name if t.category else "General",
                "description": t.description or "",
                "date": t.date.isoformat() if t.date else None
            })

        return {
            "total_balance": total_balance,
            "period": period,
            "period_income": period_totals["income"],
            "period_expense": period_totals["expense"],
            "period_savings": period_totals["net_savings"],
            "period_savings_rate": period_totals["savings_rate"],
            "total_income": all_time_totals["income"],
            "total_expenses": all_time_totals["expense"],
            "category_spending": category_spending,
            "monthly_trends": monthly_trends,
            "recent_transactions": recent_formatted,
            "health_score": health_data["health_score"],
            "health_status": health_data["status"],
            "health_metrics": health_data["metrics"]
        }
