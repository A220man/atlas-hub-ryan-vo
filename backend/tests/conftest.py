import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_local_demo_token
from app.main import create_app

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite with StaticPool for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    settings.DEMO_MODE = True
    settings.APP_ENV = "test"
    settings.DATABASE_URL = TEST_DATABASE_URL


@pytest.fixture
def db_session():
    """Create fresh database tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def analyst_token():
    return create_local_demo_token(
        sub="test-analyst",
        email="analyst@test.local",
        roles=["analyst"]
    )


@pytest.fixture
def viewer_token():
    return create_local_demo_token(
        sub="test-viewer",
        email="viewer@test.local",
        roles=["viewer"]
    )


@pytest.fixture
def admin_token():
    return create_local_demo_token(
        sub="test-admin",
        email="admin@test.local",
        roles=["admin"]
    )
