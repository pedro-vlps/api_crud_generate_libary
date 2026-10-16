"""Public request and response contracts for example items."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Validated fields accepted when creating an item."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class ItemRead(ItemCreate):
    """A database-generated identifier accompanies the item fields."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
