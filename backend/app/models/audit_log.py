from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class AuditLog(Base):
    """
    SQLAlchemy model representing a chronological log of changes made inside a workspace.
    """
    __tablename__ = "audit_log"

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # 'create', 'update', 'delete', 'invite', 'role_change', 'import', 'export'
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'transaction', 'bill', 'goal', 'budget', 'workspace'
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")
