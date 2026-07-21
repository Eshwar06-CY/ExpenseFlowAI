from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

from sqlalchemy import event

connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"timeout": 30}

# Engine configuration (connection pool parameters optimized for production)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
    connect_args=connect_args,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

# Local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    Dependency generator yielding a database session
    and automatically closing it when the request context finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
