import os
import sys
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import get_db
from app.database.base_class import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_planning.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Recreate tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_planning_flows():
    # 1. REGISTER & LOGIN
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "plan_test@expenseflow.ai",
            "full_name": "Planner Tester",
            "password": "SecurePassword123!",
        },
    )
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "plan_test@expenseflow.ai", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. CREATE ACCOUNT & CATEGORY
    acc_res = client.post(
        "/api/v1/accounts/",
        json={"name": "Checking Account", "type": "bank", "balance": 1000.0, "currency": "USD"},
        headers=headers,
    )
    assert acc_res.status_code == 201
    account_id = acc_res.json()["id"]

    seed_res = client.post("/api/v1/categories/seed", headers=headers)
    assert seed_res.status_code == 201

    cat_res = client.get("/api/v1/categories/", headers=headers)
    assert cat_res.status_code == 200
    food_cat = [c for c in cat_res.json() if c["name"] == "Food & Dining"][0]

    # 3. CREATE RECURRING RULES & BILLS
    # Create recurring salary of $3000 monthly
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    start_date = datetime.now(timezone.utc).isoformat()
    rec_res = client.post(
        "/api/v1/recurring/",
        json={
            "name": "Monthly Salary",
            "description": "Salary paycheck",
            "type": "income",
            "amount": 3000.0,
            "frequency": "monthly",
            "start_date": start_date,
            "next_run": next_week,
            "account_id": account_id,
            "category_id": food_cat["id"]
        },
        headers=headers
    )
    assert rec_res.status_code == 201

    # Create unpaid bill due in 15 days of $200
    due_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    bill_res = client.post(
        "/api/v1/bills/",
        json={
            "name": "Electric Bill",
            "amount": 200.0,
            "due_date": due_date,
            "category_id": food_cat["id"]
        },
        headers=headers
    )
    assert bill_res.status_code == 201

    # 4. TEST FORECAST PROJECTIONS BASELINE
    # Initial balance: 1000.00.
    # At day 7: salary runs -> 1000 + 3000 = 4000
    # At day 15: bill runs -> 4000 - 200 = 3800
    forecast_res = client.get("/api/v1/planning/forecast", headers=headers)
    assert forecast_res.status_code == 200
    fc = forecast_res.json()
    assert fc["balance_7d"] >= 4000.00
    assert fc["balance_30d"] >= 3800.00
    assert fc["balance_90d"] >= 9800.00 # 3 months of salary (9000) - 200 bill + 1000 balance

    # 5. CREATE WHAT-IF SCENARIOS
    # Rent increase of $500/month
    scen_res = client.post(
        "/api/v1/planning/scenarios",
        json={
            "name": "Rent Hike Scenario",
            "type": "rent_increase",
            "amount": 500.0,
            "is_active": True
        },
        headers=headers
    )
    assert scen_res.status_code == 201
    scen_id = scen_res.json()["id"]

    # Re-fetch forecast under active scenario. 90-day balance should deduct 3 months of rent hike ($1500)
    forecast_res_scen = client.get("/api/v1/planning/forecast", headers=headers)
    assert forecast_res_scen.status_code == 200
    fc_scen = forecast_res_scen.json()
    assert fc_scen["balance_90d"] <= 8300.00 # 9800 baseline - 1500 rent hike

    # Toggle scenario off
    toggle_res = client.put(f"/api/v1/planning/scenarios/{scen_id}", json={"is_active": False}, headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # Forecast should return to baseline
    forecast_res_base = client.get("/api/v1/planning/forecast", headers=headers)
    assert forecast_res_base.json()["balance_90d"] >= 9800.00

    # 6. SAVINGS GOAL PLANNER
    goal_target_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    goal_res = client.post(
        "/api/v1/goals/",
        json={
            "name": "Vacation Goal",
            "target_amount": 2400.0,
            "current_amount": 0.0,
            "target_date": goal_target_date
        },
        headers=headers
    )
    assert goal_res.status_code == 201
    goal_id = goal_res.json()["id"]

    plan_res = client.get(f"/api/v1/planning/savings/{goal_id}/plan", headers=headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert plan["remaining_amount"] == 2400.0
    assert plan["required_monthly_savings"] >= 190.0 # 2400 / ~12 months = ~200/mo

    # 7. BUDGET RECOMMENDATIONS & FINANCIAL HEALTH
    # Create a couple of mock food expenses to build average statistical outputs
    client.post(
        "/api/v1/transactions/",
        json={
            "type": "expense",
            "amount": 150.0,
            "description": "Weekly Grocery Trip",
            "category_id": food_cat["id"],
            "account_id": account_id,
            "date": datetime.now(timezone.utc).isoformat()
        },
        headers=headers
    )

    rec_budget_res = client.get("/api/v1/planning/budget-recommendations", headers=headers)
    assert rec_budget_res.status_code == 200
    recs = rec_budget_res.json()
    assert len(recs) >= 1
    assert recs[0]["category_name"] == "Food & Dining"

    health_res = client.get("/api/v1/planning/financial-health", headers=headers)
    assert health_res.status_code == 200
    assert "health_score" in health_res.json()
    assert health_res.json()["cash_reserve"] >= 800.00 # 1000 - 150 expense

    # 8. TIMELINE CHRONOLOGICAL FEED
    timeline_res = client.get("/api/v1/planning/timeline", headers=headers)
    assert timeline_res.status_code == 200
    assert len(timeline_res.json()) >= 1

    # Clean up test DB file
    if os.path.exists("./test_planning.db"):
        try:
            os.remove("./test_planning.db")
        except Exception:
            pass

if __name__ == "__main__":
    test_planning_flows()
    print("ALL ADVANCED FINANCIAL PLANNING TESTS COMPLETED SUCCESSFULLY!")
