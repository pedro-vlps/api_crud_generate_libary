"""Resolve and validate a model's single primary key."""

from typing import Any
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.orm import InstrumentedAttribute

from api_crud_generate_libary.errors import InvalidInputError


class ModelIdentity:
    """Support UUID, integer and string primary keys without assuming a name."""

    def __init__(self, model: type):
        mapper = inspect(model)
        if len(mapper.primary_key) != 1:
            raise ValueError("CRUD models must have exactly one primary key.")
        column = mapper.primary_key[0]
        self.name = mapper.get_property_by_column(column).key
        self.attribute: InstrumentedAttribute = getattr(model, self.name)
        self.python_type = column.type.python_type
        if self.python_type not in (UUID, int, str):
            raise ValueError(
                "Primary keys must use UUID, integer or string values."
            )

    def parse(self, value: str) -> UUID | int | str:
        """Convert a path identifier to the mapped Python type."""
        try:
            return self.python_type(value)
        except (ValueError, TypeError) as error:
            raise InvalidInputError("Incorrect ID format.") from error

    def value(self, record: object) -> Any:
        """Read the mapped key from a loaded record."""
        return getattr(record, self.name)
