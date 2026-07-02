"""
Database Configuration
Sets up SQLAlchemy connection to PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment.
# Local development should set DATABASE_URL explicitly instead of relying on a fallback.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Configure your production database connection string "
        "in the deployment environment (for example, Neon or Render Postgres)."
    )

# Create database engine (echo=False to disable SQL logging)
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function to get database session
    Use this in FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Call this on app startup
    """
    from .db_models import Base
    Base.metadata.create_all(bind=engine)
