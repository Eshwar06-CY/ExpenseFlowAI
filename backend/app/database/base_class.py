from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class that automatically sets
    tablenames to lowercase class names and adds common fields.
    """
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
