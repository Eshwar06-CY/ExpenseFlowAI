from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class RecurringTransaction(Base):
    """
    SQLAlchemy model representing a scheduled recurring transaction.
    """
    __tablename__ = "recurring_transaction"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'income', 'expense'
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")
    category = relationship("Category")
    account = relationship("Account")
