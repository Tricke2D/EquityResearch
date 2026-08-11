import pytest
from sqlalchemy import text

from src.equity_research_agent.db.session import SessionLocal


def test_db_connection():
    """Test koneksi ke database."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("✅ Database connection successful!")
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
    finally:
        db.close()


def test_pgvector_extension():
    """Test bahwa pgvector extension sudah aktif."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        assert result.scalar() == "vector"
        print("✅ pgvector extension is active!")
    except Exception as e:
        pytest.fail(f"pgvector extension not found: {e}")
    finally:
        db.close()