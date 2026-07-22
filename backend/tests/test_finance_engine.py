from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

import app.database.base
from app.database.base import Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.bill import Bill
from app.models.category import Category
from app.services.finance_engine import FinanceEngine
from app.core.security import get_password_hash

DATABASE_URL = "sqlite:///./test_finance_engine.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _seed_test_data():
    db = TestingSessionLocal()
    user = User(
        email="engine_user@example.com",
        full_name="Engine Tester",
        password_hash=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    account1 = Account(user_id=user.id, name="Checking", type="checking", balance=5000.0)
    account2 = Account(user_id=user.id, name="Savings", type="savings", balance=10000.0)
    db.add_all([account1, account2])
    db.commit()
    db.refresh(account1)
    db.refresh(account2)

    cat_food = Category(user_id=user.id, name="Food & Dining", type="expense", color="#FF5733")
    cat_salary = Category(user_id=user.id, name="Salary", type="income", color="#33FF57")
    db.add_all([cat_food, cat_salary])
    db.commit()
    db.refresh(cat_food)
    db.refresh(cat_salary)

    now = datetime.now()
    tx1 = Transaction(
        user_id=user.id,
        account_id=account1.id,
        category_id=cat_salary.id,
        type="income",
        amount=4000.0,
        date=now - timedelta(days=5)
    )
    tx2 = Transaction(
        user_id=user.id,
        account_id=account1.id,
        category_id=cat_food.id,
        type="expense",
        amount=1000.0,
        date=now - timedelta(days=3)
    )
    db.add_all([tx1, tx2])

    budget = Budget(user_id=user.id, category_id=cat_food.id, amount=1500.0, spent=1000.0, month="2026-07")
    bill = Bill(user_id=user.id, name="Internet Bill", amount=100.0, due_date=now + timedelta(days=10), is_paid=True)
    db.add_all([budget, bill])
    db.commit()

    user_id = user.id
    db.close()
    return user_id


def test_get_active_balance():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        balance = FinanceEngine.get_active_balance(db, user_id)
        assert balance == 15000.0
    finally:
        db.close()


def test_get_period_totals_and_division_by_zero_safety():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        totals = FinanceEngine.get_period_totals(db, user_id)
        assert totals["income"] == 4000.0
        assert totals["expense"] == 1000.0
        assert totals["net_savings"] == 3000.0
        assert totals["savings_rate"] == 75.0  # (3000 / 4000) * 100

        # Edge case: zero income
        empty_user_id = 9999
        empty_totals = FinanceEngine.get_period_totals(db, empty_user_id)
        assert empty_totals["income"] == 0.0
        assert empty_totals["savings_rate"] == 0.0  # Safe 0.0 instead of ZeroDivisionError
    finally:
        db.close()


def test_get_category_spending():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        spending = FinanceEngine.get_category_spending(db, user_id)
        assert len(spending) == 1
        assert spending[0]["category"] == "Food & Dining"
        assert spending[0]["amount"] == 1000.0
        assert spending[0]["percentage"] == 100.0
    finally:
        db.close()


def test_get_budget_adherence_and_bill_reliability():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        budgets = FinanceEngine.get_budget_adherence(db, user_id)
        assert budgets["total_budgets"] == 1
        assert budgets["exceeded_budgets"] == 0
        assert budgets["adherence_rate_pct"] == 100.0

        bills = FinanceEngine.get_bill_reliability(db, user_id)
        assert bills["total_bills"] == 1
        assert bills["paid_bills"] == 1
        assert bills["reliability_rate_pct"] == 100.0
    finally:
        db.close()


def test_calculate_financial_health_score():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        health = FinanceEngine.calculate_financial_health_score(db, user_id)
        assert 0 <= health["health_score"] <= 100
        assert health["status"] in ["Excellent", "Healthy", "Critical"]
        assert health["metrics"]["savings_rate_pct"] == 75.0
        assert health["metrics"]["budget_adherence_pct"] == 100.0
    finally:
        db.close()


def test_get_dashboard_summary():
    user_id = _seed_test_data()
    db = TestingSessionLocal()
    try:
        summary = FinanceEngine.get_dashboard_summary(db, user_id, period="30d")
        assert summary["total_balance"] == 15000.0
        assert summary["period_income"] == 4000.0
        assert summary["period_expense"] == 1000.0
        assert summary["period_savings"] == 3000.0
        assert summary["health_score"] >= 80
        assert len(summary["category_spending"]) == 1
        assert len(summary["monthly_trends"]) == 6
    finally:
        db.close()
