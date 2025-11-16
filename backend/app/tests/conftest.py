"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis.asyncio as aioredis

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, generate_api_key
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async test engine
test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Create async session maker
TestAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create all tables
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session

    # Drop all tables
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        api_key=generate_api_key(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser."""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("AdminPassword123"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        api_key=generate_api_key(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_organization(db_session: AsyncSession, test_user: User) -> Organization:
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        description="A test organization",
        owner_id=test_user.id,
    )
    db_session.add(org)

    # Add user to organization
    test_user.organization_id = org.id

    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_project(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User
) -> Project:
    """Create a test project."""
    project = Project(
        name="Test Project",
        slug="test-project",
        description="A test project",
        organization_id=test_organization.id,
        created_by=test_user.id,
        tags=["test", "demo"],
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authentication headers for test user."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def superuser_headers(test_superuser: User) -> dict:
    """Get authentication headers for superuser."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_superuser.id))
    return {"Authorization": f"Bearer {token}"}
