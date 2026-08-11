from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.equity_research_agent.config import DATABASE_URL
from src.equity_research_agent.db.models import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency untuk mendapatkan session database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Buat semua tabel di database."""
    Base.metadata.create_all(bind=engine)