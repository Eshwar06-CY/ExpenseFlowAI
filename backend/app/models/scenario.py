from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Scenario(Base):
    """
    SQLAlchemy model representing a "What If" financial planning scenario.
    """
    __tablename__ = "scenario"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'salary_increase', 'spend_reduction', 'rent_increase', 'one_off_purchase'
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True)
    percent_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    one_off_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")
    category = relationship("Category")
