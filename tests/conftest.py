import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.dependencies import get_arq_queue
from unittest.mock import MagicMock, AsyncMock

# Base de données de test séparée
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:1234@db:5432/slotapi_test"
)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with session_factory() as session:
            yield session
            
    async def override_get_arq_queue():
        return AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_arq_queue] = override_get_arq_queue
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_arq_queue, None)
    await engine.dispose()

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as ac:
        yield ac

@pytest.fixture
def api_key():
    return settings.API_KEY