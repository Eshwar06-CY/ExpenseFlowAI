# ExpenseFlow AI

> "Track smarter. Save better."

ExpenseFlow AI is a modern, production-ready SaaS application designed to help businesses, developers, and teams track outflows, analyze cash flow trends, and utilize AI insights to reduce expense leakages. 

This repository serves as a clean-architecture foundation for future features, separating the backend (FastAPI/SQLAlchemy) and the frontend (React/Vite/Tailwind CSS) into modular, decoupled service directories.

---

## ⚡ Tech Stack

### Frontend
- **Framework:** React 18 (bootstrapped with Vite)
- **Routing:** React Router v6
- **Styling:** Tailwind CSS with modern custom variables, custom scrollbars, and glassmorphic panels
- **HTTP Client:** Axios (configured with token request/response interceptors)
- **Icons:** Lucide React

### Backend
- **Framework:** FastAPI (Python 3.11)
- **ORM:** SQLAlchemy 2.0 (configured with optimized pool settings)
- **Configuration & Validation:** Pydantic v2 & Pydantic Settings
- **Authentication (Ready):** JWT creation & BCrypt hashing signature hooks
- **Database Driver:** PyMySQL (MySQL 8.0 support)

### Operations
- **Containerization:** Docker & Docker Compose setup

---

## 📂 Project Architecture

```
ExpenseFlowAI/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── core/             # Configuration, logging and security logic
│   │   ├── database/         # Session setup and declarative bases
│   │   ├── middleware/       # Custom application middleware (CORS)
│   │   ├── models/           # SQLAlchemy DB Models (Future expansion)
│   │   ├── routers/          # Versioned API routes endpoints
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Core business logic handlers
│   │   ├── utils/            # Helper scripts
│   │   └── main.py           # Application Entrypoint (lifespan hook, startup, routers)
│   ├── .env.example          # Environment variables template
│   ├── Dockerfile            # Python app containerization
│   └── requirements.txt      # Backend Python dependencies
├── frontend/                 # React SPA Application
│   ├── src/
│   │   ├── assets/           # Images, logos, and illustration resources
│   │   ├── components/       # Layout structures & common design atoms (Buttons/Cards)
│   │   ├── context/          # React context providers (AuthContext)
│   │   ├── hooks/            # Custom hooks
│   │   ├── layouts/          # Page layouts (Dashboard shells)
│   │   ├── pages/            # View pages (Login, Register, Dashboard, Analytics, etc.)
│   │   ├── services/         # HTTP Api Client instances
│   │   ├── styles/           # CSS & global styling variables
│   │   ├── App.jsx           # App shell and routing tree
│   │   └── main.jsx          # DOM rendering entrypoint
│   ├── .env.example          # Frontend env settings
│   ├── index.html            # Main markup page template
│   ├── tailwind.config.js    # Tailwind layout utility overrides
│   ├── postcss.config.js     # PostCSS setup
│   ├── vite.config.js        # Vite compiler configurations
│   └── Dockerfile            # Node build steps
├── docs/                     # Design documentations & specifications
├── screenshots/              # Mock screenshots & diagrams
├── docker-compose.yml        # Development multi-container script
├── .gitignore                # Global git ignored directories
└── README.md                 # Project README
```

---

## 🚀 Installation & Local Development

### Prerequisites
Make sure you have [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/) installed on your machine.

### Quick Start with Docker
To bring up the entire stack (FastAPI backend, React frontend, MySQL 8.0 instance) with a single command:

1. Clone or navigate to the repository:
   ```bash
   cd D:/Antigravity_Projects/ExpenseFlowAI
   ```

2. Generate local environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. Spin up the containers:
   ```bash
   docker-compose up --build
   ```

Once built, you can access the applications at:
- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Backend API Root:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Development Workflow

### Local Backend Setup (No Docker)
If you prefer to run the FastAPI app locally inside a virtual environment:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up database credentials in `.env`.
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Local Frontend Setup (No Docker)
To run the Vite dev server locally:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Boot the development server:
   ```bash
   npm run dev
   ```

### Running E2E Test Suite (Playwright)
To execute the automated end-to-end integration and regression test suites:

1. Ensure the development backend and frontend services are active.
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Run the test suite:
   ```bash
   # Run all E2E test suites in parallel
   npm run test:e2e

   # Run tests in Playwright interactive UI mode
   npx playwright test --ui
   ```

---

## 🔒 Authentication & Users System (Phase 2)

ExpenseFlow AI uses a secure JWT token rotation system:
1. **Access Tokens:** Transferred via `Authorization: Bearer <JWT>` header (valid for 60 minutes).
2. **Refresh Tokens:** Transferred via request body and cached locally in browser storage (valid for 7 days).
3. **Password Security:** Multi-layered regex strength rules enforced via Pydantic model validators, and hashed using direct `bcrypt` salting.

### API Specifications

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | Register a new user profile with email validation & strength rules. | No |
| `POST` | `/api/v1/auth/login` | Authenticate user credentials and return access + refresh tokens. | No |
| `POST` | `/api/v1/auth/refresh` | Rotate and issue new access & refresh tokens. | No |
| `POST` | `/api/v1/auth/logout` | Client logout helper. | No |
| `GET`  | `/api/v1/users/me` | Retrieve the authenticated user profile metadata. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/users/profile` | Update display name, email details, or password credentials. | Yes (Bearer Access) |
| `GET`  | `/api/v1/accounts/` | List all accounts for the active user. | Yes (Bearer Access) |
| `POST` | `/api/v1/accounts/` | Create a new account (bank, cash, credit). | Yes (Bearer Access) |
| `PUT`  | `/api/v1/accounts/{id}` | Update account details (name, type, balance). | Yes (Bearer Access) |
| `DELETE` | `/api/v1/accounts/{id}` | Delete account (cascade deletes all related transactions). | Yes (Bearer Access) |
| `GET`  | `/api/v1/categories/` | List categories (combines custom and system defaults). | Yes (Bearer Access) |
| `POST` | `/api/v1/categories/` | Create a custom category. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/categories/{id}` | Update custom category name, icon, or color. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/categories/{id}` | Delete custom category. | Yes (Bearer Access) |
| `POST` | `/api/v1/categories/seed` | Seed default expense/income templates for user. | Yes (Bearer Access) |
| `GET`  | `/api/v1/transactions/` | List transactions with paging, search, type, and account filters. | Yes (Bearer Access) |
| `POST` | `/api/v1/transactions/` | Log transaction (income, expense, transfer) and reconcile balance. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/transactions/{id}` | Edit transaction and automatically adjust account balances. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/transactions/{id}` | Delete transaction and rollback account balance changes. | Yes (Bearer Access) |
| `GET`  | `/api/v1/transactions/stats` | Retrieve aggregated totals, savings rates, and SVG chart data. | Yes (Bearer Access) |
| `GET`  | `/api/v1/budgets/` | List all budgets for user in specified month (defaults to current). | Yes (Bearer Access) |
| `POST` | `/api/v1/budgets/` | Create a category budget limit for a month (auto-syncs spent total). | Yes (Bearer Access) |
| `PUT`  | `/api/v1/budgets/{id}` | Adjust budget limit amount. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/budgets/{id}` | Delete a budget limit. | Yes (Bearer Access) |
| `GET`  | `/api/v1/goals/` | List all savings goals for user. | Yes (Bearer Access) |
| `POST` | `/api/v1/goals/` | Create a new savings goal. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/goals/{id}` | Update savings goal metadata or target. | Yes (Bearer Access) |
| `POST` | `/api/v1/goals/{id}/contribute` | Add savings contribution (optional account debit double-entry). | Yes (Bearer Access) |
| `DELETE` | `/api/v1/goals/{id}` | Delete a savings goal. | Yes (Bearer Access) |
| `GET`  | `/api/v1/bills/` | List bills, optionally filtered by paid/unpaid status. | Yes (Bearer Access) |
| `POST` | `/api/v1/bills/` | Register a new pending bill with due date. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/bills/{id}` | Update bill attributes. | Yes (Bearer Access) |
| `POST` | `/api/v1/bills/{id}/pay` | Settle a bill from account (logs transaction & adjusts balance). | Yes (Bearer Access) |
| `DELETE` | `/api/v1/bills/{id}` | Delete a scheduled bill. | Yes (Bearer Access) |
| `GET`  | `/api/v1/recurring/` | List active recurring transaction schedules. | Yes (Bearer Access) |
| `POST` | `/api/v1/recurring/` | Schedule a recurring transaction rule (weekly, monthly, yearly). | Yes (Bearer Access) |
| `POST` | `/api/v1/recurring/process` | Run scheduler engine to automatically post due recurring transactions. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/recurring/{id}` | Update recurring schedule properties. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/recurring/{id}` | Delete a recurring schedule rule. | Yes (Bearer Access) |
| `GET`  | `/api/v1/notifications/` | List notifications, optionally filtered by read/unread status. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/notifications/{id}/read` | Mark a specific notification as read. | Yes (Bearer Access) |
| `PUT`  | `/api/v1/notifications/read-all` | Mark all unread notifications as read. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/notifications/{id}` | Dismiss/Delete a notification. | Yes (Bearer Access) |
| `GET`  | `/api/v1/reports/monthly` | Compile and download in-memory formatted monthly statement PDF. | Yes (Bearer Access) |
| `POST` | `/api/v1/insights/generate` | Trigger Insights Engine analysis pipeline (trends, patterns, forecasts). | Yes (Bearer Access) |
| `GET`  | `/api/v1/insights/` | Retrieve generated cash flow trends, recurring matches, and health scores. | Yes (Bearer Access) |
| `GET`  | `/api/v1/insights/events` | List active undismissed financial warning alerts. | Yes (Bearer Access) |
| `POST` | `/api/v1/insights/events/{id}/dismiss` | Dismiss an alert from dashboard. | Yes (Bearer Access) |
| `GET`  | `/api/v1/insights/briefing/daily` | Retrieve structured daily financial health briefings. | Yes (Bearer Access) |

| `POST` | `/api/v1/import/upload` | Parse CSV/Excel statement file headers and return raw preview rows. | Yes (Bearer Access) |
| `POST` | `/api/v1/import/analyze` | Run custom column mapping, category suggestion, and duplicate detection. | Yes (Bearer Access) |
| `POST` | `/api/v1/import/execute` | Commit imported transactions batch with duplicate actions (Skip/Replace/Merge). | Yes (Bearer Access) |
| `GET`  | `/api/v1/import/history` | List statement upload jobs history. | Yes (Bearer Access) |
| `POST` | `/api/v1/import/history/{id}/rollback` | Roll back an import batch, deleting transactions and reverting balances. | Yes (Bearer Access) |
| `GET`  | `/api/v1/import/templates` | List saved column mapping configurations. | Yes (Bearer Access) |
| `POST` | `/api/v1/import/templates` | Save a new column mapping template. | Yes (Bearer Access) |
| `DELETE` | `/api/v1/import/templates/{id}` | Delete a saved mapping template. | Yes (Bearer Access) |
| `GET`  | `/api/v1/reports/analytics/summary` | KPI summary: income, expense, net, savings rate, avg daily spend, vs prior period. | Yes |
| `GET`  | `/api/v1/reports/analytics/cash-flow` | Time-bucketed income vs expense vs net (day/week/month grouping). | Yes |
| `GET`  | `/api/v1/reports/analytics/categories` | Category spending/income distribution for donut charts. | Yes |
| `GET`  | `/api/v1/reports/analytics/merchants` | Top merchants by expense volume. | Yes |
| `GET`  | `/api/v1/reports/analytics/net-worth` | Monthly cumulative net worth trend (12 months). | Yes |
| `GET`  | `/api/v1/reports/analytics/budget-adherence` | Budget vs actual spend per category for current month. | Yes |
| `POST` | `/api/v1/automation/rules` | Create an automation rule (IF→THEN conditions and actions). | Yes |
| `GET`  | `/api/v1/automation/rules` | List all automation rules for the user. | Yes |
| `PATCH` | `/api/v1/automation/rules/{id}` | Update rule name, conditions, actions, priority. | Yes |
| `DELETE` | `/api/v1/automation/rules/{id}` | Delete a rule and its execution history. | Yes |
| `POST` | `/api/v1/automation/rules/{id}/enable` | Enable an automation rule. | Yes |
| `POST` | `/api/v1/automation/rules/{id}/disable` | Disable an automation rule. | Yes |
| `POST` | `/api/v1/automation/rules/{id}/run` | Manually trigger a scheduled automation rule. | Yes |
| `POST` | `/api/v1/automation/test` | Dry-run a rule against existing transactions without committing. | Yes |
| `GET`  | `/api/v1/automation/executions` | Execution history (filterable by rule and status). | Yes |
| `GET`  | `/api/v1/automation/stats` | Aggregate automation statistics. | Yes |
| `GET`  | `/api/v1/workspaces/` | List all workspaces the user belongs to. | Yes |
| `POST` | `/api/v1/workspaces/` | Create a new workspace. | Yes |
| `POST` | `/api/v1/workspaces/{id}/invite` | Invite a member to a workspace by email. | Yes |
| `POST` | `/api/v1/workspaces/invite/{token}/accept` | Accept a workspace invitation via token. | Yes |
| `DELETE` | `/api/v1/workspaces/{id}/members/{uid}` | Remove a member from a workspace. | Yes |
| `GET`  | `/api/v1/planning/forecast` | Project balance at 7/30/90 days using recurring transactions. | Yes |
| `POST` | `/api/v1/planning/scenario` | Simulate "What If" financial scenarios (income change, new expense). | Yes |

---

## 🗺️ Roadmap & Deployment

- [x] **Phase 1: Foundation** — Scaffolding, routing, Docker Compose, layout design system.
- [x] **Phase 2: Database & Auth** — Alembic migrations, JWT auth, bcrypt passwords.
- [x] **Phase 3: Financial Core CRUD** — Transactions, accounts, categories, transfers, dashboard KPIs.
- [x] **Phase 4: Financial Planning** — Budgets, goals, bills, recurring schedules, PDF statements.
- [x] **Phase 5: Financial Intelligence** — Cash flow engine, subscription scanner, briefing builder, health score.
- [x] **Phase 6: Production Hardening** — Middleware stack, rate limiting, security headers, audit logging, CI.
- [x] **Phase 7: Smart Import** — CSV/Excel import wizard, column mapping, duplicate detection, rollback.
- [x] **Phase 8: Enterprise SaaS Polish** — Enriched dashboard, quick actions, activity timeline, spending trends.
- [x] **Phase 9: Advanced Planning** — Cash flow forecast (7/30/90d), What-If scenario simulator.
- [x] **Phase 10: Shared Workspaces** — Multi-user workspaces, role-based access, invitations, audit trail.
- [x] **Phase 11: Automation Engine** — Visual rule builder (IF→THEN), 11 operators, 7 action types, APScheduler, 36 tests.
- [x] **Phase 12: Analytics & Reporting** — Live Recharts dashboard (area, donut, line, bar), 6 KPIs, period picker, budget adherence, merchant analysis.
- [x] **Phase 13: E2E Testing & Quality Assurance** — Playwright test framework, robust Page Objects, parallel worker database synchronization, 21 automated regression tests for authentication, accounts, categories, transactions, and transfers.

For more information, see:
* [API Reference](file:///d:/Antigravity_Projects/ExpenseFlowAI/docs/API.md)
* [System Architecture](file:///d:/Antigravity_Projects/ExpenseFlowAI/docs/ARCHITECTURE.md)
* [Production Deployment](file:///d:/Antigravity_Projects/ExpenseFlowAI/docs/DEPLOYMENT.md)
* [Contributing Guide](file:///d:/Antigravity_Projects/ExpenseFlowAI/CONTRIBUTING.md)
* [Data Import Guide](file:///d:/Antigravity_Projects/ExpenseFlowAI/docs/IMPORT_GUIDE.md)
