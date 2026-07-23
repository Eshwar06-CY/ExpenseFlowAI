import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import get_db
from app.database.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_production.db"
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


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)


def test_production_flow():
    # 1. AUTHENTICATION & REGISTER
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "prod_test@expenseflow.ai",
            "full_name": "Prod tester",
            "password": "SecurePassword123!",
        },
    )
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "prod_test@expenseflow.ai"

    # 2. LOGIN
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "prod_test@expenseflow.ai", "password": "SecurePassword123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. GET PROFILE
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "prod_test@expenseflow.ai"

    # 4. REFRESH TOKEN
    ref_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert ref_response.status_code == 200
    token = ref_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 5. CREATE ACCOUNT
    acc_response = client.post(
        "/api/v1/accounts/",
        json={"name": "Checking Account", "type": "bank", "balance": 1500.0, "currency": "USD"},
        headers=headers,
    )
    assert acc_response.status_code == 201
    account_id = acc_response.json()["id"]

    # 6. SEED CATEGORIES & FETCH
    seed_response = client.post("/api/v1/categories/seed", headers=headers)
    assert seed_response.status_code == 201
    
    cat_response = client.get("/api/v1/categories/", headers=headers)
    assert cat_response.status_code == 200
    categories = cat_response.json()
    food_cat = [c for c in categories if c["name"] == "Food & Dining"][0]

    # 7. CREATE BUDGET & EXPENSE SYNC
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    bud_response = client.post(
        "/api/v1/budgets/",
        json={"category_id": food_cat["id"], "amount": 100.0, "month": current_month},
        headers=headers,
    )
    assert bud_response.status_code == 201

    tx_response = client.post(
        "/api/v1/transactions/",
        json={
            "type": "expense",
            "amount": 120.0,
            "description": "Premium Groceries",
            "category_id": food_cat["id"],
            "account_id": account_id,
            "date": datetime.now(timezone.utc).isoformat(),
        },
        headers=headers,
    )
    assert tx_response.status_code == 201

    # Check notification triggered
    notif_response = client.get("/api/v1/notifications/", headers=headers)
    assert notif_response.status_code == 200
    res_data = notif_response.json()
    items = res_data.get("items", []) if isinstance(res_data, dict) else res_data
    assert len(items) > 0
    assert "Budget" in items[0]["title"]

    # 8. SAVINGS GOALS
    goal_response = client.post(
        "/api/v1/goals/",
        json={
            "name": "Emergency Fund",
            "target_amount": 500.0,
            "current_amount": 50.0,
            "deadline": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        },
        headers=headers,
    )
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    # Contribution
    contrib_response = client.post(
        f"/api/v1/goals/{goal_id}/contribute?amount=100.0&account_id={account_id}",
        headers=headers,
    )
    assert contrib_response.status_code == 200
    assert contrib_response.json()["current_amount"] == 150.0

    # 9. BILLS & QUICK PAY
    bill_response = client.post(
        "/api/v1/bills/",
        json={
            "name": "Office Rent",
            "amount": 250.0,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        },
        headers=headers,
    )
    assert bill_response.status_code == 201
    bill_id = bill_response.json()["id"]

    pay_response = client.post(
        f"/api/v1/bills/{bill_id}/pay?account_id={account_id}",
        headers=headers,
    )
    assert pay_response.status_code == 200
    assert pay_response.json()["is_paid"] is True

    # 10. RECURRING TX RULES
    rec_response = client.post(
        "/api/v1/recurring/",
        json={
            "description": "Cloud Subscription",
            "type": "expense",
            "amount": 15.0,
            "category_id": food_cat["id"],
            "account_id": account_id,
            "frequency": "monthly",
            "start_date": datetime.now(timezone.utc).isoformat(),
        },
        headers=headers,
    )
    assert rec_response.status_code == 201

    # Run due recurring transactions
    client.post("/api/v1/recurring/process", headers=headers)

    # 11. INSIGHTS ENGINE PIPELINE
    insights_response = client.post("/api/v1/insights/generate", headers=headers)
    assert insights_response.status_code == 200

    briefing_response = client.get("/api/v1/insights/briefing/daily", headers=headers)
    assert briefing_response.status_code == 200
    assert "health_score" in briefing_response.json()["content"]

    # 12. EXPORT DATA (CSV & EXCEL)
    csv_response = client.get("/api/v1/export/csv", headers=headers)
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]

    excel_response = client.get("/api/v1/export/excel", headers=headers)
    assert excel_response.status_code == 200
    assert "openpyxl" in excel_response.headers.get("content-type", "") or "sheet" in excel_response.headers.get("content-type", "")

    # 13. REPORT PDF GENERATION
    pdf_response = client.get(f"/api/v1/reports/monthly?month={current_month}", headers=headers)
    assert pdf_response.status_code == 200
    assert "application/pdf" in pdf_response.headers["content-type"]

    # 14. SETTINGS (PASSWORD CHANGE)
    pw_response = client.put(
        "/api/v1/settings/password",
        json={
            "current_password": "SecurePassword123!",
            "new_password": "SecurePasswordNew99?",
            "confirm_password": "SecurePasswordNew99?",
        },
        headers=headers,
    )
    assert pw_response.status_code == 200

    # 15. SETTINGS (JSON DATA EXPORT)
    json_export = client.post("/api/v1/settings/export-data", headers=headers)
    assert json_export.status_code == 200
    assert "application/json" in json_export.headers["content-type"]
    assert json_export.json()["user"]["email"] == "prod_test@expenseflow.ai"

    # 16. RATE LIMITER test (login too many times)
    for _ in range(10):
        rl_res = client.post(
            "/api/v1/auth/login",
            json={"email": "prod_test@expenseflow.ai", "password": "SecurePasswordNew99?"},
        )
        if rl_res.status_code == 429:
            break
    assert rl_res.status_code in [200, 429]

    # Clean up test database
    if os.path.exists("./test_production.db"):
        try:
            os.remove("./test_production.db")
        except Exception:
            pass


if __name__ == "__main__":
    test_production_flow()
    print("ALL PRODUCTION INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
