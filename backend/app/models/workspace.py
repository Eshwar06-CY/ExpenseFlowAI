from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class Workspace(Base):
    """
    SQLAlchemy model representing an isolated Workspace.
    """
    __tablename__ = "workspace"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    """
    SQLAlchemy model representing a member's association with a Workspace.
    """
    __tablename__ = "workspace_member"

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)  # 'owner', 'admin', 'editor', 'viewer'
    invited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])
