import os
import sys
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project path to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.session import get_db
from app.database.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_import.db"
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

def test_import_and_export_flows():
    # 1. REGISTER USER
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "import_test@expenseflow.ai",
            "full_name": "Importer Tester",
            "password": "SecurePassword123!",
        },
    )
    assert reg_res.status_code == 201

    # 2. LOGIN
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "import_test@expenseflow.ai", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. CREATE ACCOUNT
    acc_res = client.post(
        "/api/v1/accounts/",
        json={"name": "Checking Account", "type": "bank", "balance": 1000.0, "currency": "USD"},
        headers=headers,
    )
    assert acc_res.status_code == 201
    account_id = acc_res.json()["id"]

    # 4. UPLOAD CSV FILE FOR PREVIEW
    csv_data = "Transaction Date,Amount,Description\n2026-07-10,-50.25,Uber Ride\n2026-07-11,2500.00,Stripe Transfer\n"
    files = {"file": ("test_statement.csv", csv_data, "text/csv")}
    upload_res = client.post("/api/v1/import/upload", files=files, headers=headers)
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert "headers" in data
    assert "rows" in data
    assert "Transaction Date" in data["headers"]
    assert len(data["rows"]) == 2

    # 5. ANALYZE COLUMNS (SUGGESTIONS & VALIDATION & DUPLICATE)
    analyze_payload = {
        "rows": data["rows"],
        "mapping": {
            "date_col": "Transaction Date",
            "amount_col": "Amount",
            "desc_col": "Description"
        },
        "account_id": account_id
    }
    analyze_res = client.post("/api/v1/import/analyze", json=analyze_payload, headers=headers)
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert "rows" in analysis
    assert len(analysis["rows"]) == 2
    
    # Assert offline category suggestions
    uber_row = [r for r in analysis["rows"] if "Uber" in r["description"]][0]
    assert uber_row["suggested_category_name"] == "Transportation"

    # 6. EXECUTE THE IMPORT BATCH
    execute_payload = {
        "filename": "test_statement.csv",
        "duplicate_action": "skip",
        "rows": [
            {
                "date": "2026-07-10T00:00:00",
                "amount": 50.25,
                "description": "Uber Ride",
                "category_id": uber_row["suggested_category_id"],
                "account_id": account_id,
                "type": "expense",
                "is_duplicate": False
            },
            {
                "date": "2026-07-11T00:00:00",
                "amount": 2500.00,
                "description": "Stripe Transfer",
                "account_id": account_id,
                "type": "income",
                "is_duplicate": False
            }
        ]
    }
    exec_res = client.post("/api/v1/import/execute", json=execute_payload, headers=headers)
    assert exec_res.status_code == 200
    job_info = exec_res.json()
    assert job_info["rows_imported"] == 2
    assert job_info["status"] == "completed"
    import_id = job_info["id"]

    # Verify account balance reconciled (1000 - 50.25 + 2500 = 3449.75)
    chk_res = client.get("/api/v1/accounts/", headers=headers)
    assert chk_res.status_code == 200
    account_info = [a for a in chk_res.json() if a["id"] == account_id][0]
    assert account_info["balance"] == 3449.75

    # 7. DUPLICATE DETECTION CHECK (Re-analyzing the same rows should detect duplicate items)
    re_analyze_res = client.post("/api/v1/import/analyze", json=analyze_payload, headers=headers)
    assert re_analyze_res.status_code == 200
    re_analysis = re_analyze_res.json()
    assert re_analysis["duplicate_count"] == 2

    # 8. MAPPING TEMPLATES CRUD
    tpl_create_res = client.post(
        "/api/v1/import/templates",
        json={
            "name": "Custom Chase Format",
            "date_col": "Transaction Date",
            "amount_col": "Amount",
            "desc_col": "Description"
        },
        headers=headers
    )
    assert tpl_create_res.status_code == 200
    tpl_id = tpl_create_res.json()["id"]

    # Get templates list
    tpl_get_res = client.get("/api/v1/import/templates", headers=headers)
    assert tpl_get_res.status_code == 200
    assert len(tpl_get_res.json()) >= 1

    # Delete template
    tpl_del_res = client.delete(f"/api/v1/import/templates/{tpl_id}", headers=headers)
    assert tpl_del_res.status_code == 204

    # 9. EXPORTS CHECK (CSV, Excel, PDF)
    # CSV export
    export_csv = client.get("/api/v1/export/csv", headers=headers)
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]

    # Excel export
    export_xlsx = client.get("/api/v1/export/excel", headers=headers)
    assert export_xlsx.status_code == 200

    # PDF export
    export_pdf = client.get("/api/v1/export/pdf", headers=headers)
    assert export_pdf.status_code == 200
    assert "application/pdf" in export_pdf.headers["content-type"]

    # 10. ROLLBACK IMPORT BATCH
    rollback_res = client.post(f"/api/v1/import/history/{import_id}/rollback", headers=headers)
    assert rollback_res.status_code == 200

    # Verify balance restored back to 1000.00
    chk_res_after = client.get("/api/v1/accounts/", headers=headers)
    assert chk_res_after.status_code == 200
    account_info_after = [a for a in chk_res_after.json() if a["id"] == account_id][0]
    assert account_info_after["balance"] == 1000.00

    # Clean up test DB file
    if os.path.exists("./test_import.db"):
        try:
            os.remove("./test_import.db")
        except Exception:
            pass

if __name__ == "__main__":
    test_import_and_export_flows()
    print("ALL IMPORT & DATA MANAGEMENT TESTS COMPLETED SUCCESSFULLY!")
