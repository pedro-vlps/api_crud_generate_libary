"""Isolated PostgreSQL models used by CRUD regression tests."""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Metadata owned only by the integration test schema."""


class Category(Base):
    """Referenced record with an integer primary key."""

    __tablename__ = "categories"
    category_key: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(Base):
    """Record with UUID, uniqueness, length and foreign-key constraints."""

    __tablename__ = "items"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(20), unique=True)
    description: Mapped[str] = mapped_column(
        String(100), default="default description"
    )
    category_key: Mapped[int | None] = mapped_column(
        ForeignKey("categories.category_key", ondelete="RESTRICT"),
    )
    category: Mapped[Category | None] = relationship(back_populates="items")


class StringRecord(Base):
    """Record demonstrating a non-id string primary key."""

    __tablename__ = "string_records"
    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(40))


class ItemRequest(BaseModel):
    """Requests intentionally do not provide OpenAPI examples."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    description: str
    category_key: int | None = None


class ItemResponse(ItemRequest):
    """A loaded ORM record can be serialized without implicit I/O."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID


class CategoryResponse(BaseModel):
    """Category response contract."""

    model_config = ConfigDict(from_attributes=True)
    category_key: int
    name: str


class ItemWithCategory(ItemResponse):
    """Eager scalar relationship response."""

    category: CategoryResponse | None


class CategoryWithItems(CategoryResponse):
    """Eager collection relationship response."""

    items: list[ItemResponse]


class CategoryWithNestedItems(CategoryResponse):
    """Nested eager loading response for category -> items -> category."""

    items: list[ItemWithCategory]
