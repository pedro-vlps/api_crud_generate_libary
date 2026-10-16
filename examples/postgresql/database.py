"""Configure PostgreSQL connections and their lifetime."""

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = os.environ["DATABASE_URL"]
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise ValueError("DATABASE_URL must use postgresql+asyncpg://.")

engine = create_async_engine(DATABASE_URL)
sessions = async_sessionmaker(engine, expire_on_commit=True)


async def database_session() -> AsyncIterator[AsyncSession]:
    """The application owns session creation and cleanup."""
    async with sessions() as session:
        yield session
