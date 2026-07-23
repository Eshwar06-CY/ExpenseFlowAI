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

## Completed (100% Commercial Release Ready - 20/20 Modules Verified)
- Authentication & JWT Authorization
- Official Google Gemini 2.5 Flash Migration (`google-genai` SDK v2.14.0)
- Real-Time Token Streaming & First-Token Response (`generate_content_stream`)
- Abstract AI Provider Factory & Zero-Hallucination FinanceEngine Math Guardrails
- 20-Module Feature Verification Matrix Audit (183/183 Pytest Tests Passed)
- Flagship 12-Scene Cinematic Product Journey & Signature AI Orb (`AIOrb.jsx`)
- Immersive 3D WebGL Particle Node Backgrounds & Motion System
- Premium SaaS UI/UX Design System & Global Command Palette (`Cmd+K` / `Ctrl+K`)
- Explainable AI (XAI) Framework & Interactive "Why?" Panels
- AI Financial Command Center Dashboard
- Real-Time Streaming AI Chat (Google Gemini 2.5 Flash / SSE)
- AI Financial Digest System & Bank-Grade PDF Reports (ReportLab)
- Smart Notification & Financial Alert Center
- FinanceEngine Core (Health Score, Net Worth, Cashflow)
- AI Financial Strategy Planner & Digital Twin Simulator
- Predictive Cash Flow Engine & Risk Monitoring
- Personalization & Privacy Center ("Forget Everything", Data Export)
- Accounts, Transactions, Budgets, Goals, Bills
- Automations & Rule Engine
- Workspaces & Multi-User Collaboration
- Docker & CI/CD Pipeline

## Coming Soon
- OCR Receipt Scanner
- Native Mobile App (React Native)
- PWA Support

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
