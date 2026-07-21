from typing import Optional
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Budget(Base):
    """
    SQLAlchemy model representing a category budget limit.
    """
    __tablename__ = "budget"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # "YYYY-MM" format
    
    user = relationship("User")
    workspace = relationship("Workspace")
    category = relationship("Category")
