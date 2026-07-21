from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

class ImportTemplate(Base):
    """
    SQLAlchemy model representing user mapping templates for parsing CSV/Excel statements.
    """
    __tablename__ = "import_template"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_col: Mapped[str] = mapped_column(String(100), nullable=True)
    amount_col: Mapped[str] = mapped_column(String(100), nullable=True)
    desc_col: Mapped[str] = mapped_column(String(100), nullable=True)
    cat_col: Mapped[str] = mapped_column(String(100), nullable=True)
    acc_col: Mapped[str] = mapped_column(String(100), nullable=True)
    ref_col: Mapped[str] = mapped_column(String(100), nullable=True)

    user = relationship("User")
    workspace = relationship("Workspace")
