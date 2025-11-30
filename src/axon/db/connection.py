"""Database connection management."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from axon.config import get_settings


@lru_cache
def get_engine():
    """Create async database engine (cached)."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level == "DEBUG",
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory():
    """Create async session factory (cached)."""
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Module-level session factory for easy access
session_factory = None


def _init_session_factory():
    """Initialize the module-level session factory."""
    global session_factory
    if session_factory is None:
        session_factory = get_session_factory()
    return session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    factory = _init_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()

