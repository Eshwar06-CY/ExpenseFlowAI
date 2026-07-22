# Import all models here so that Alembic can detect their metadata automatically
from app.database.base_class import Base
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.recurring import RecurringTransaction
from app.models.notification import Notification
from app.models.insight import FinancialInsight, FinancialEvent, DailyBriefing
from app.models.import_history import ImportHistory
from app.models.mapping_template import ImportTemplate
from app.models.scenario import Scenario
from app.models.workspace import Workspace, WorkspaceMember
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.automation import AutomationRule, AutomationExecution
from app.models.password_reset import PasswordResetToken
from app.models.email_verification import EmailVerificationToken

# Export for clean access
__all__ = [
    "Base",
    "User",
    "Account",
    "Category",
    "Transaction",
    "Budget",
    "Goal",
    "Bill",
    "RecurringTransaction",
    "Notification",
    "FinancialInsight",
    "FinancialEvent",
    "DailyBriefing",
    "ImportHistory",
    "ImportTemplate",
    "Scenario",
    "Workspace",
    "WorkspaceMember",
    "AuditLog",
    "Comment",
    "AutomationRule",
    "AutomationExecution",
    "PasswordResetToken",
    "EmailVerificationToken",
]

