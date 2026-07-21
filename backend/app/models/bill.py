from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Bill(Base):
    """
    SQLAlchemy model representing a pending bill or upcoming payment.
    """
    __tablename__ = "bill"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    user = relationship("User")
    workspace = relationship("Workspace")
    category = relationship("Category")
