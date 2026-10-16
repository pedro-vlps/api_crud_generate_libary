"""Build ORM reads, eager relationship loads and validated sorting."""

from typing import Any, NotRequired, TypedDict

from sqlalchemy import Select, inspect, select
from sqlalchemy.orm import InstrumentedAttribute

from api_crud_generate_libary.errors import InvalidInputError
from api_crud_generate_libary.helpers.join_load_builder import (
    build_joinedload_chain,
)


class JoinParameters(TypedDict):
    """Eager relationship path with legacy join metadata accepted."""

    response_parameter: InstrumentedAttribute
    model: NotRequired[type]
    column: NotRequired[str]


class SecondLevelJoinParameters(TypedDict):
    """Nested eager relationship path with legacy metadata accepted."""

    response_parameter: list[InstrumentedAttribute]
    first_model: NotRequired[type]
    second_model: NotRequired[type]
    column: NotRequired[str]


def build_read_query(
    model: type,
    joins: list[JoinParameters] | None = None,
    nested_joins: list[SecondLevelJoinParameters] | None = None,
) -> Select[Any]:
    """Load relationships without multiplying root rows before pagination."""
    query = select(model)
    for join in joins or []:
        query = query.options(
            build_joinedload_chain([join["response_parameter"]])
        )
    for join in nested_joins or []:
        query = query.options(
            build_joinedload_chain(join["response_parameter"])
        )
    return query


def apply_sorting(
    query: Select[Any],
    model: type,
    fields: list[str] | None,
    directions: list[str] | None,
) -> Select[Any]:
    """Reject incomplete sorting and non-column attributes."""
    if fields is None and directions is None:
        return query
    if not fields or not directions or len(fields) != len(directions):
        raise InvalidInputError(
            "Provide matching order_by and direction values."
        )
    columns = inspect(model).column_attrs
    for field, direction in zip(fields, directions, strict=True):
        if field not in columns:
            raise InvalidInputError(f"Invalid order_by field: {field}")
        column = getattr(model, field)
        if direction.lower() == "asc":
            query = query.order_by(column.asc())
        elif direction.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            raise InvalidInputError(
                "Invalid order direction. Use 'asc' or 'desc'."
            )
    return query
