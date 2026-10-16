"""Transport-independent failures exposed by CRUD operations."""


class CrudError(Exception):
    """Base exception for expected CRUD failures."""


class InvalidInputError(CrudError):
    """A query or identifier is invalid."""


class ItemNotFoundError(CrudError):
    """The requested database record does not exist."""


class ConstraintConflictError(CrudError):
    """A database integrity constraint prevents an operation."""


class InvalidDataError(CrudError):
    """A value cannot be stored in its database column."""


class DatabaseUnavailableError(CrudError):
    """The database cannot currently serve the request."""


class DatabaseOperationError(CrudError):
    """An unexpected database operation failed."""
