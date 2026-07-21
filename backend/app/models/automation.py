"""
AutomationRule and AutomationExecution SQLAlchemy models.

AutomationRule stores user-defined IF→THEN rules as JSON.
AutomationExecution stores the outcome of each rule run.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class AutomationRule(Base):
    """
    Represents a user-defined automation rule.

    conditions: JSON array of condition objects
        [{"field": "description", "operator": "contains", "value": "Uber"}, ...]

    actions: JSON array of action objects
        [{"type": "assign_category", "category_id": 3}, ...]

    condition_logic: "AND" (all conditions must match) or "OR" (any condition)
    trigger: when the rule fires
        "on_transaction" | "daily" | "weekly" | "monthly" | "on_bill_due" | "on_goal_completed"
    priority: lower number = higher priority (runs first)
    """
    __tablename__ = "automation_rule"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Trigger
    trigger: Mapped[str] = mapped_column(
        String(50), default="on_transaction", nullable=False
    )  # on_transaction | daily | weekly | monthly | on_bill_due | on_goal_completed

    # Condition tree
    condition_logic: Mapped[str] = mapped_column(
        String(10), default="AND", nullable=False
    )  # "AND" | "OR"
    conditions: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON

    # Actions
    actions: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON

    # Stats
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User")
    executions = relationship(
        "AutomationExecution", back_populates="rule", cascade="all, delete-orphan"
    )


class AutomationExecution(Base):
    """
    Records the result of a single automation rule run.
    """
    __tablename__ = "automation_execution"

    rule_id: Mapped[int] = mapped_column(
        ForeignKey("automation_rule.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transaction.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "success" | "failed" | "skipped"
    actions_executed: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON list of action types that ran
    result_summary: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    rule = relationship("AutomationRule", back_populates="executions")
    user = relationship("User")
