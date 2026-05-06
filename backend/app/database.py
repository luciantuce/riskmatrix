from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# ---------------------------------------------------------------------------
# Engine setup
# ---------------------------------------------------------------------------
# SQLite requires `check_same_thread=False` for multi-threaded access.
# Postgres benefits from a connection pool sized for our expected concurrency.
# ---------------------------------------------------------------------------
if settings.is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # survive DB restarts / idle disconnects
        pool_size=5,  # baseline connections
        max_overflow=10,  # burst capacity
        pool_recycle=1800,  # recycle after 30 min to dodge stale conns
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
