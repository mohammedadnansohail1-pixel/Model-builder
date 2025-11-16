"""Pytest configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
import uuid

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.models.model_registry import ModelRegistry, ModelType, ModelSource
from app.models.dataset import Dataset, DatasetFormat, ValidationStatus
from app.models.training import TrainingJob, TrainingConfig, TrainingStatus, FineTuningMethod
from app.core.security import get_password_hash

# Use test database
TEST_DATABASE_URL = "postgresql+asyncpg://universaltune:universaltune_password@localhost:5432/universaltune_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession, test_user: User) -> Organization:
    """Create test organization."""
    org = Organization(
        id=uuid.uuid4(),
        name="Test Organization",
        slug="test-org",
        created_by=test_user.id
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User, test_organization: Organization) -> Project:
    """Create test project."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_model(db_session: AsyncSession, test_user: User) -> ModelRegistry:
    """Create test model."""
    model = ModelRegistry(
        id=uuid.uuid4(),
        name="Test Model",
        model_type=ModelType.LLM,
        model_id="test/model",
        source=ModelSource.HUGGINGFACE,
        created_by=test_user.id
    )
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)
    return model


@pytest_asyncio.fixture
async def test_dataset(db_session: AsyncSession, test_user: User, test_project: Project) -> Dataset:
    """Create test dataset."""
    dataset = Dataset(
        id=uuid.uuid4(),
        name="Test Dataset",
        project_id=test_project.id,
        format=DatasetFormat.JSON,
        file_path="s3://test/dataset.json",
        size_bytes=1024,
        size_rows=100,
        validation_status=ValidationStatus.VALID,
        created_by=test_user.id
    )
    db_session.add(dataset)
    await db_session.commit()
    await db_session.refresh(dataset)
    return dataset


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Get authentication headers."""
    from app.core.security import create_access_token

    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
