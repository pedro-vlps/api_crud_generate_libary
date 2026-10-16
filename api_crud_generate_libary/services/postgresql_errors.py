"""Translate PostgreSQL driver failures without exposing database details."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from asyncpg import PostgresError
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api_crud_generate_libary.errors import (
    ConstraintConflictError,
    CrudError,
    DatabaseOperationError,
    DatabaseUnavailableError,
    InvalidDataError,
)


def translate_database_error(error: Exception) -> CrudError:
    """Classify SQLSTATE, including asyncpg errors wrapped by SQLAlchemy."""
    original = error.orig if isinstance(error, DBAPIError) else error
    sqlstate = getattr(original, "sqlstate", None)
    if isinstance(error, IntegrityError) or (
        sqlstate and sqlstate.startswith("23")
    ):
        return ConstraintConflictError(
            "The operation violates a database constraint."
        )
    if sqlstate and sqlstate.startswith("22"):
        return InvalidDataError("A value is invalid for its database column.")
    if (isinstance(error, DBAPIError) and error.connection_invalidated) or (
        sqlstate and sqlstate.startswith(("08", "53", "57"))
    ):
        return DatabaseUnavailableError(
            "The database is temporarily unavailable."
        )
    return DatabaseOperationError("The database operation failed.")


@asynccontextmanager
async def database_operation(session: AsyncSession) -> AsyncIterator[None]:
    """Restore a failed session; the caller owns its lifetime."""
    try:
        yield
    except (SQLAlchemyError, PostgresError) as error:
        await session.rollback()
        raise translate_database_error(error) from error
