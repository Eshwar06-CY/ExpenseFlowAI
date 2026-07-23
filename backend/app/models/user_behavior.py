"""
UserBehavior Models - ExpenseFlowAI Personalization & Privacy Center
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class UserLearnedBehavior(Base):
    """
    SQLAlchemy model storing individual learned behavioral observations for a user with confidence scores.
    Allows targeted deletion ("Forget This Behavior").
    """
    __tablename__ = "user_learned_behavior"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Dining, Savings, Bills, Goals
    observation: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Frequently exceeds budget."
    confidence: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)  # e.g., 0.91 (91%)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")


class UserBehaviorEvent(Base):
    """
    SQLAlchemy model recording application-level user behavioral events and recommendation responses.
    """
    __tablename__ = "user_behavior_event"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
