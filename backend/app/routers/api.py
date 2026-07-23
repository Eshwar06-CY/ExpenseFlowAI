from fastapi import APIRouter
from app.routers import auth, users, accounts, categories, transactions, budgets, goals, bills, recurring_tx, notifications, reports, insights, export, settings, health, import_data, search, planning_router as planning, collaboration, automation, ai, personalization, chat_stream, dashboard_overview, digests, explanations

api_router = APIRouter()

# Register routes
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(dashboard_overview.router, prefix="/dashboard", tags=["command-center"])
api_router.include_router(digests.router, tags=["digests"])
api_router.include_router(explanations.router, tags=["explanations"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(bills.router, prefix="/bills", tags=["bills"])
api_router.include_router(recurring_tx.router, prefix="/recurring", tags=["recurring"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(import_data.router, prefix="/import", tags=["import"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(planning.router, prefix="/planning", tags=["planning"])
api_router.include_router(collaboration.router, prefix="/workspaces", tags=["collaboration"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(chat_stream.router, tags=["chat-stream"])
api_router.include_router(personalization.router, tags=["personalization"])
api_router.include_router(health.router, tags=["health"])

