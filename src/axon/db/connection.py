"""Database connection management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from axon.config import get_settings


def get_engine():
    """Create async database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level == "DEBUG",
        pool_pre_ping=True,
    )


def get_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    engine = get_engine()
    session_factory = get_session_factory(engine)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

