"""Compose eager loading for SQLAlchemy relationship attributes."""

from collections.abc import Sequence

from sqlalchemy.orm import InstrumentedAttribute, Load, joinedload


def build_joinedload_chain(path_list: Sequence[InstrumentedAttribute]) -> Load:
    """Chain mapped relationships; strings and empty paths are invalid."""
    if not path_list:
        raise ValueError("A relationship path cannot be empty.")
    if any(
        not isinstance(attribute, InstrumentedAttribute)
        for attribute in path_list
    ):
        raise ValueError("Relationship paths must contain mapped attributes.")
    loader = joinedload(path_list[0])
    for attribute in path_list[1:]:
        loader = loader.joinedload(attribute)
    return loader
