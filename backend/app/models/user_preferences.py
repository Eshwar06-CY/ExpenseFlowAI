"""
UserPreferences Model - ExpenseFlowAI Adaptive Financial Intelligence
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class UserPreferences(Base):
    """
    SQLAlchemy model storing user-level AI personalization settings and learned behavioral preferences.
    """
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    communication_style: Mapped[str] = mapped_column(String(50), default="concise", nullable=False)
    category_sensitivities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    ignored_recommendation_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list string
    auto_reminder_lead_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    user = relationship("User")
