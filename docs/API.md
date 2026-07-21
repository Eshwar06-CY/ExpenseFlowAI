# ExpenseFlow AI — API Documentation

This document describes all API endpoints available in the ExpenseFlow AI backend. All endpoints are prefixed with `/api/v1`.

---

## 🔐 Authentication Module (`/auth`)

### 1. Register User
- **Method:** `POST`
- **Path:** `/auth/register`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "SecurePassword123!",
    "profile_picture": "https://example.com/avatar.jpg"
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "profile_picture": "https://example.com/avatar.jpg",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-07-19T00:00:00Z"
  }
  ```

### 2. Login
- **Method:** `POST`
- **Path:** `/auth/login`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### 3. Refresh Token
- **Method:** `POST`
- **Path:** `/auth/refresh`
- **Request Body:**
  ```json
  {
    "refresh_token": "eyJhbGciOi..."
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

## 🏦 Accounts Module (`/accounts`)

*All requests require a `Authorization: Bearer <token>` header.*

### 1. List Accounts
- **Method:** `GET`
- **Path:** `/accounts/`
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 1,
      "name": "Checking Account",
      "type": "bank",
      "balance": 1500.0,
      "currency": "USD"
    }
  ]
  ```

### 2. Create Account
- **Method:** `POST`
- **Path:** `/accounts/`
- **Request Body:**
  ```json
  {
    "name": "Savings Stash",
    "type": "savings",
    "balance": 2500.0,
    "currency": "USD"
  }
  ```
- **Response:** `201 Created`

---

## 📝 Ledger Transactions Module (`/transactions`)

### 1. Create Transaction
- **Method:** `POST`
- **Path:** `/transactions/`
- **Request Body:**
  ```json
  {
    "type": "expense",
    "amount": 42.50,
    "description": "Weekly Groceries",
    "category_id": 4,
    "account_id": 1,
    "date": "2026-07-19T09:00:00Z"
  }
  ```
- **Response:** `201 Created`

### 2. Get Transaction Statistics
- **Method:** `GET`
- **Path:** `/transactions/stats`
- **Response:** `200 OK`
  ```json
  {
    "total_balance": 3957.50,
    "total_income": 4000.00,
    "total_expenses": 42.50,
    "savings": 3957.50,
    "category_spending": [
      {
        "category": "Food & Dining",
        "color": "#EF4444",
        "amount": 42.50
      }
    ],
    "recent_transactions": [...]
  }
  ```

---

## 📊 Exports & Reports Module (`/export`, `/reports`)

### 1. Export CSV
- **Method:** `GET`
- **Path:** `/export/csv`
- **Query Parameters (Optional):** `start_date`, `end_date`, `category_id`, `account_id`, `type`, `ids`
- **Response:** `200 OK` (Streamed CSV download file)

### 2. Export Excel
- **Method:** `GET`
- **Path:** `/export/excel`
- **Query Parameters (Optional):** `start_date`, `end_date`, `category_id`, `account_id`, `type`, `ids`
- **Response:** `200 OK` (Streamed XLSX download file)

### 3. Export PDF
- **Method:** `GET`
- **Path:** `/export/pdf`
- **Query Parameters (Optional):** `start_date`, `end_date`, `category_id`, `account_id`, `type`, `ids`
- **Response:** `200 OK` (Streamed PDF download file)

### 4. Monthly PDF Statement
- **Method:** `GET`
- **Path:** `/reports/monthly`
- **Query Parameters (Required):** `month=YYYY-MM`
- **Response:** `200 OK` (Streamed PDF download file)

---

## 📥 Bank Statement Import Module (`/import`)

### 1. Upload file preview
- **Method:** `POST`
- **Path:** `/import/upload`
- **Request:** Form-data with `file` (CSV or XLSX)
- **Response:** `200 OK`
  ```json
  {
    "headers": ["Date", "Amount", "Description"],
    "rows": [
      {"Date": "2026-07-10", "Amount": "-50.25", "Description": "Uber Ride"}
    ]
  }
  ```

### 2. Analyze mapped rows
- **Method:** `POST`
- **Path:** `/import/analyze`
- **Request Body:**
  ```json
  {
    "rows": [{"Date": "2026-07-10", "Amount": "-50.25", "Description": "Uber Ride"}],
    "mapping": {"date_col": "Date", "amount_col": "Amount", "desc_col": "Description"},
    "account_id": 1
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "rows": [
      {
        "original_row": {"Date": "2026-07-10", "Amount": "-50.25", "Description": "Uber Ride"},
        "date": "2026-07-10T00:00:00",
        "amount": -50.25,
        "description": "Uber Ride",
        "is_duplicate": false,
        "suggested_category_id": 4,
        "suggested_category_name": "Transportation"
      }
    ],
    "duplicate_count": 0,
    "error_count": 0
  }
  ```

### 3. Execute final import
- **Method:** `POST`
- **Path:** `/import/execute`
- **Request Body:**
  ```json
  {
    "filename": "statement.csv",
    "duplicate_action": "skip",
    "rows": [
      {
        "date": "2026-07-10T00:00:00",
        "amount": 50.25,
        "description": "Uber Ride",
        "category_id": 4,
        "account_id": 1,
        "type": "expense"
      }
    ]
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "id": 1,
    "filename": "statement.csv",
    "rows_imported": 1,
    "rows_skipped": 0,
    "rows_failed": 0,
    "status": "completed"
  }
  ```

### 4. Import History list
- **Method:** `GET`
- **Path:** `/import/history`
- **Response:** `200 OK`

### 5. Rollback import batch
- **Method:** `POST`
- **Path:** `/import/history/{id}/rollback`
- **Response:** `200 OK`
  ```json
  {
    "success": true,
    "message": "Import batch successfully rolled back."
  }
  ```

### 6. Mapping Templates (GET/POST/DELETE)
- **Endpoints:** `/import/templates` and `/import/templates/{id}`

---

## ⚙️ Settings Module (`/settings`)

### 1. Change Password
- **Method:** `PUT`
- **Path:** `/settings/password`
- **Response:** `200 OK`

### 2. Full Data Export
- **Method:** `POST`
- **Path:** `/settings/export-data`
- **Response:** `200 OK`

### 3. Account Deactivation
- **Method:** `DELETE`
- **Path:** `/settings/account`
- **Response:** `200 OK`

---

## 📈 Advanced Financial Planning Module (`/planning`)

### 1. Cash Flow Projections
- **Method:** `GET`
- **Path:** `/planning/forecast`
- **Response:** `200 OK`
  ```json
  {
    "balance_7d": 1500.00,
    "balance_30d": 3500.00,
    "balance_90d": 9500.00,
    "monthly_surplus": 2000.00,
    "timeline": [
      {"date": "2026-07-20", "balance": 1500.00}
    ]
  }
  ```

### 2. Scenario Simulator CRUD
- **Endpoints:**
  - `GET /planning/scenarios` (List What-If rules)
  - `POST /planning/scenarios` (Create What-If rule)
  - `PUT /planning/scenarios/{id}` (Update What-If parameters)
  - `DELETE /planning/scenarios/{id}` (Delete What-If rule)
- **Request Body Example (POST):**
  ```json
  {
    "name": "Rent Hike",
    "type": "rent_increase",
    "amount": 500.00,
    "is_active": true
  }
  ```
- **Response:** `201 Created`

### 3. Savings Goal Planner suggestions
- **Method:** `GET`
- **Path:** `/planning/savings/{goal_id}/plan`
- **Response:** `200 OK`
  ```json
  {
    "target_amount": 2400.00,
    "current_amount": 400.00,
    "remaining_amount": 2000.00,
    "required_monthly_savings": 200.00,
    "estimated_completion_date": "2027-05-20",
    "progress_timeline": [
      {"date": "2026-08-20", "expected_amount": 600.00}
    ]
  }
  ```

### 4. Category Budget Recommendations
- **Method:** `GET`
- **Path:** `/planning/budget-recommendations`
- **Response:** `200 OK`
  ```json
  [
    {
      "category_id": 4,
      "category_name": "Food & Dining",
      "avg_monthly_spending": 220.00,
      "recommended_budget": 240.00,
      "current_budget": 200.00,
      "status": "overspending_risk"
    }
  ]
  ```

### 5. Financial Health Metrics
- **Method:** `GET`
- **Path:** `/planning/financial-health`
- **Response:** `200 OK`
  ```json
  {
    "health_score": 85,
    "savings_rate": 22.5,
    "expense_ratio": 77.5,
    "income_stability": 95.0,
    "emergency_fund_coverage_months": 3.2,
    "budget_adherence_rate": 88.0,
    "cash_reserve": 12500.00,
    "historical_health_trend": [
      {"month": "Jul 2026", "score": 85}
    ]
  }
  ```

### 6. Unified chronological timeline
- **Method:** `GET`
- **Path:** `/planning/timeline`
- **Response:** `200 OK`
  ```json
  [
    {
      "date": "2026-07-19",
      "type": "transaction_expense",
      "title": "Weekly Grocery Trip",
      "description": "Ledger entries reconciliation on account.",
      "amount": -150.00
    }
  ]
  ```
