"""Standard file for application schemas setup"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
# from pydantic.generics import GenericModel

# Generic type to dynamically replace
T = TypeVar("T")

class PatternSchemaDataList(BaseModel, Generic[T]):
    """Schema for GET requests with pagination and optional total count."""
    data: list[T]
    total_count: Optional[int] = None
    has_more: Optional[bool] = None

class PatternSchema(BaseModel, Generic[T]):
    """Generic schema for API responses."""
    data: T

class PatternGetSchema(BaseModel, Generic[T]):
    """Schema for GET requests with pagination and optional total count."""
    data: list[T]
