from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Goal(Base):
    """
    SQLAlchemy model representing a savings goal.
    """
    __tablename__ = "goal"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User")
    workspace = relationship("Workspace")
