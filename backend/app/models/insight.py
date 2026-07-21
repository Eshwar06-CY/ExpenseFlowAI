from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Boolean, JSON, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class FinancialInsight(Base):
    """
    SQLAlchemy model representing structured financial analysis findings.
    """
    __tablename__ = "financial_insight"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'trend', 'health', 'pattern', 'forecast'
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Structured details
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")

class FinancialEvent(Base):
    """
    SQLAlchemy model representing notable financial activities or warnings.
    """
    __tablename__ = "financial_event"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'large_expense', 'savings_drop', 'upcoming_bill'
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # 'low', 'medium', 'high'
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")

class DailyBriefing(Base):
    """
    SQLAlchemy model representing structured daily briefing packets.
    """
    __tablename__ = "daily_briefing"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # Structured daily brief details
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")
