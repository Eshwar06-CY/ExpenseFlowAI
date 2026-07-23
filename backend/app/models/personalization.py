"""
Personalization Models - ExpenseFlowAI Personalization & Privacy Center
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class AIPersonalizationSettings(Base):
    """
    SQLAlchemy model storing user-level AI personalization, coaching, and privacy preferences.
    """
    __tablename__ = "ai_personalization_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # 1. AI Settings
    enable_ai_personalization: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_ai_learning: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    coaching_style: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)  # friendly, professional, motivational
    recommendation_frequency: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)  # every_login, daily, weekly, important_only
    response_detail: Mapped[str] = mapped_column(String(50), default="balanced", nullable=False)  # brief, balanced, detailed
    
    enable_smart_suggestions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_goal_recommendations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_spending_insights: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 4. Privacy Center Controls
    enable_memory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_behavior_tracking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_goal_tracking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_communication_preference_learning: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
