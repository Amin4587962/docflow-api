from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""


# Create async engine using DATABASE_URL from settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

# Factory for async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for each request."""
    async with AsyncSessionLocal() as session:
        yield session
