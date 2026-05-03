from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import User
from main import app


@pytest.fixture
def db():
    """In-memory SQLite test DB with full schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """FastAPI TestClient with database dependency override."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # Avoid running seed startup against non-test database.
    app.router.on_startup.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_user(db):
    """Default authenticated user entity used by auth tests."""
    user = User(clerk_user_id="user_test_123", email="test@example.com", role="client")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, "Bearer fake.jwt.token"
