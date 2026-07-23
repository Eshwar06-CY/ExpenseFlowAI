"""
AIMemory SQLAlchemy Model - ExpenseFlowAI

Stores structured persistent memories, user goals, preferences, and lifestyle context
across chat sessions while respecting user privacy controls.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class AIMemory(Base):
    __tablename__ = "ai_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    
    category = Column(String(50), nullable=False, index=True)  # financial_goal, savings_preference, budget_preference, risk_preference, lifestyle_note, conversation_summary, user_decision
    key = Column(String(100), nullable=False, index=True)       # e.g. macbook_goal, relocation_city, risk_profile
    value = Column(Text, nullable=False)                        # e.g. MacBook Pro M4, Bangalore, Moderate risk tolerance
    confidence = Column(Float, default=1.0, nullable=False)     # Confidence score (0.0 to 1.0)
    is_active = Column(Boolean, default=True, nullable=False)   # Soft delete / user toggle flag
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", backref="ai_memories")

    __table_args__ = (
        Index("ix_user_memory_category_key", "user_id", "category", "key"),
    )

    def __repr__(self):
        return f"<AIMemory(id={self.id}, user_id={self.user_id}, category='{self.category}', key='{self.key}')>"
