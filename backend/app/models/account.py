from typing import Optional
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Account(Base):
    """
    SQLAlchemy model representing a financial account (e.g. Bank Account, Cash, Credit Card).
    """
    __tablename__ = "account"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'bank', 'cash', 'credit'
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")
