from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class PasswordResetToken(Base):
    """
    SQLAlchemy model for password reset tokens.
    Tokens are single-use, expire after 1 hour, and are tied to a user_id.
    """
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
