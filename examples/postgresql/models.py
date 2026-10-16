"""Database records for the example item context."""

from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Example database metadata."""


class Item(Base):
    """An item with a generated UUID and a unique name."""

    __tablename__ = "example_items"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
