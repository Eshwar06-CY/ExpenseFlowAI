from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Transaction(Base):
    """
    SQLAlchemy model representing a financial ledger entry (Income, Expense, or Transfer).
    """
    __tablename__ = "transaction"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'income', 'expense', 'transfer'
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), nullable=True, index=True)
    to_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"), nullable=True, index=True)
    import_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_history.id", ondelete="SET NULL"), nullable=True, index=True)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    
    user = relationship("User")
    workspace = relationship("Workspace")
    category = relationship("Category")
    account = relationship("Account", foreign_keys=[account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
    import_history = relationship("ImportHistory")
