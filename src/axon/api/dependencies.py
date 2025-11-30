"""FastAPI dependencies for database and other shared resources."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.connection import get_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()

