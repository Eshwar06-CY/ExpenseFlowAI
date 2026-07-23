"""
SQLAlchemy Model for AI Financial Digest - ExpenseFlowAI
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base


class FinancialDigest(Base):
    """
    SQLAlchemy model representing a compiled financial digest (daily, weekly, monthly, yearly)
    and its generated PDF report path.
    """
    __tablename__ = "financial_digest"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    digest_type: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False, index=True)  # daily, weekly, monthly, yearly
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    health_score: Mapped[int] = mapped_column(Integer, default=88, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
