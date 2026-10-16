"""Stable response envelopes for individual records and listings."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PatternSchemaDataList(BaseModel, Generic[T]):
    """Wrap records, with optional pagination metadata."""

    data: list[T]
    total_count: int | None = None
    has_more: bool | None = None


class PatternSchema(BaseModel, Generic[T]):
    """Wrap a single record."""

    data: T
