from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Category(Base):
    """
    SQLAlchemy model representing a transaction category (e.g. Food, Salary, Transport).
    """
    __tablename__ = "category"
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'income', 'expense', 'both'
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    user = relationship("User")
