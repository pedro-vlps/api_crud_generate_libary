"""Build PATCH contracts while preserving field validation and nullability."""

from copy import copy

from pydantic import BaseModel, create_model


def create_partial_schema(schema: type[BaseModel]) -> type[BaseModel]:
    """Make fields omittable without accepting null for non-nullable fields."""
    fields = {}
    for name, field in schema.model_fields.items():
        optional_field = copy(field)
        optional_field.default = None
        optional_field.default_factory = None
        optional_field.validate_default = False
        fields[name] = (field.annotation, optional_field)
    return create_model(f"{schema.__name__}Partial", __base__=schema, **fields)
