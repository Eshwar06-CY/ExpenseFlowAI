"""
SQLAlchemy Models for Notifications and User Notification Preferences - ExpenseFlowAI
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class Notification(Base):
    """
    SQLAlchemy model representing a smart prioritized notification.
    Categories: budget, bills, goals, forecast, ai, security, system, achievements
    Priorities: critical, high, medium, low
    """
    __tablename__ = "notification"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="system", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User")


class NotificationPreference(Base):
    """
    SQLAlchemy model representing a user's notification delivery preferences.
    """
    __tablename__ = "notification_preference"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    enable_budget_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_bill_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_goal_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_forecast_warnings: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_ai_recommendations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_security_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_achievements: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_in_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    digest_frequency: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
