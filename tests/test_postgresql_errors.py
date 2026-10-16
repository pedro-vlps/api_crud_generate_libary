"""Verify SQLSTATE classification and session recovery without leaking SQL."""

from unittest.mock import AsyncMock

import pytest
from asyncpg import (
    CannotConnectNowError,
    PostgresError,
    StringDataRightTruncationError,
    UniqueViolationError,
)
from sqlalchemy.exc import DBAPIError, IntegrityError

from api_crud_generate_libary.errors import (
    ConstraintConflictError,
    DatabaseOperationError,
    DatabaseUnavailableError,
    InvalidDataError,
)
from api_crud_generate_libary.services.postgresql_errors import (
    database_operation,
    translate_database_error,
)


@pytest.mark.parametrize(
    "original,expected",
    [
        (UniqueViolationError("private constraint"), ConstraintConflictError),
        (StringDataRightTruncationError("private value"), InvalidDataError),
        (CannotConnectNowError("private server"), DatabaseUnavailableError),
        (PostgresError("private query"), DatabaseOperationError),
    ],
)
def test_wrapped_sqlstate_classification(original, expected):
    """SQLAlchemy wrappers retain the PostgreSQL SQLSTATE classification."""
    error = DBAPIError("private SQL", {"password": "private"}, original)
    translated = translate_database_error(error)
    assert isinstance(translated, expected)
    assert "private" not in str(translated)


async def test_failed_write_rolls_back():
    """A failed database operation restores the caller-owned session."""
    session = AsyncMock()
    failure = IntegrityError("private SQL", {}, UniqueViolationError())
    with pytest.raises(ConstraintConflictError):
        async with database_operation(session):
            raise failure
    session.rollback.assert_awaited_once()
    session.close.assert_not_awaited()
