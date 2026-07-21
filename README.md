# 💰 ExpenseFlowAI

## AI-Powered Personal Finance Platform

**Track • Analyze • Forecast • Automate • Grow**

A modern full-stack SaaS application built with **React**, **FastAPI**, **MySQL**, **SQLAlchemy**, **Docker**, and **Playwright**.

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker)
![Playwright](https://img.shields.io/badge/Playwright-E2E-2EAD33?logo=playwright)

---

# 📖 Overview

ExpenseFlowAI is a production-ready personal finance platform that helps users manage accounts, budgets, transactions, analytics, reports, automation, and AI-powered financial insights.

## ✨ Features

### 💳 Finance
- Accounts
- Income
- Expenses
- Transfers
- Categories

### 📊 Analytics
- Dashboard
- Reports
- Spending Analysis
- Cash Flow
- Forecasting

### 🎯 Planning
- Budgets
- Goals
- Bills
- Recurring Transactions

### 🤖 AI
- Smart Insights
- Recommendations
- Financial Health

### ⚙ Automation
- Import Wizard
- CSV Import
- Automation Rules

### 👥 Collaboration
- Workspaces
- Notifications

---

# 🏗 Architecture

```text
User
 │
 ▼
React + Vite
 │
 ▼
FastAPI
 │
 ▼
SQLAlchemy
 │
 ▼
MySQL
 │
 ▼
AI Intelligence
```

# 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Auth | JWT |
| Testing | Playwright |
| DevOps | Docker + GitHub Actions |

# 📂 Project Structure

```text
ExpenseFlowAI/
├── backend/
├── frontend/
├── docs/
├── screenshots/
└── docker-compose.yml
```

# ⚙ Installation

```bash
git clone https://github.com/YOUR_USERNAME/ExpenseFlowAI.git
cd ExpenseFlowAI

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up --build
```

Frontend: http://localhost:5173

Backend: http://localhost:8000

Swagger: http://localhost:8000/docs

# 🧪 Testing

```bash
cd frontend
npm run test:e2e
```

Includes E2E tests for Authentication, Dashboard, Accounts, Categories, Transactions, and Transfers.

# 📸 Screenshots

Create:

- docs/images/dashboard.png
- docs/images/login.png
- docs/images/analytics.png
- docs/images/reports.png

# 🗺 Roadmap

## Completed
- Authentication
- Dashboard
- Accounts
- Transactions
- Budgets
- Goals
- Reports
- Docker
- Playwright

## Coming Soon
- AI Chat
- OCR Receipt Scanner
- Mobile App
- PWA

# 📚 Documentation

```
docs/
├── API.md
├── Architecture.md
├── Deployment.md
├── Testing.md
```

# 🤝 Contributing

Contributions are welcome.

# 📄 License

MIT License

---

⭐ Star the repository if you like the project!
