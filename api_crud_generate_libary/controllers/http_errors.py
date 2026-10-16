"""Map expected CRUD failures to HTTP responses at the transport boundary."""

from collections.abc import Awaitable
from typing import TypeVar

from fastapi import HTTPException

from api_crud_generate_libary.errors import (
    ConstraintConflictError,
    CrudError,
    DatabaseOperationError,
    DatabaseUnavailableError,
    InvalidDataError,
    InvalidInputError,
    ItemNotFoundError,
)

T = TypeVar("T")
ERROR_STATUS = {
    InvalidInputError: 400,
    InvalidDataError: 400,
    ItemNotFoundError: 404,
    ConstraintConflictError: 409,
    DatabaseUnavailableError: 503,
    DatabaseOperationError: 500,
}


async def execute_http(operation: Awaitable[T]) -> T:
    """Expose safe domain messages without leaking driver exceptions."""
    try:
        return await operation
    except CrudError as error:
        raise HTTPException(
            status_code=ERROR_STATUS.get(type(error), 500),
            detail=str(error),
        ) from error
