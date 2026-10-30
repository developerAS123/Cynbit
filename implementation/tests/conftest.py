import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from implementation.core.database import Base, get_db
from implementation.core.security import hash_password
from implementation.models.entities import User
from implementation.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

test_session_factory = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a clean in-memory database session for each test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with test_session_factory() as session:
        yield session
        await session.rollback()
        
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Provides an authenticated/unauthenticated ASGI test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
        
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Seeds a test user with an Argon2id hashed password."""
    user = User(
        email="intern@cynbit.in",
        hashed_password=hash_password("SuperSecretPassword123!"),
        full_name="Test Intern",
        role="intern",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
