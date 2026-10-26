import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.account import Account
from app.models.transaction import Transaction

# Determine test database URL
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL", settings.TEST_DATABASE_URL or settings.DATABASE_URL
)

try:
    test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    USING_POSTGRES = True
except Exception:
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    USING_POSTGRES = False

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def is_postgres():
    return USING_POSTGRES


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up database tables after each test for pristine isolation
        session.rollback()
        session.query(Transaction).delete()
        session.query(Account).delete()
        session.commit()
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def created_account(client) -> dict:
    response = client.post("/accounts", json={"name": "Test User"})
    assert response.status_code == 201
    return response.json()
