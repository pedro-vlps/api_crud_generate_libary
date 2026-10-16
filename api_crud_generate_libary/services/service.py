"""Persist CRUD records using caller-owned PostgreSQL async sessions."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from api_crud_generate_libary.errors import InvalidInputError, ItemNotFoundError
from api_crud_generate_libary.queries.model_identity import ModelIdentity
from api_crud_generate_libary.queries.read_query import (
    JoinParameters,
    SecondLevelJoinParameters,
    apply_sorting,
    build_read_query,
)
from api_crud_generate_libary.services.postgresql_errors import (
    database_operation,
)

M = TypeVar("M")


class Service(Generic[M]):
    """Execute CRUD; mutations commit without closing the session."""

    def __init__(self, table_model: type[M]):
        self.table_model = table_model
        self.identity = ModelIdentity(table_model)

    async def read(
        self,
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
        page: int | None = None,
        items_per_page: int | None = None,
        order_by: list[str] | None = None,
        direction: list[str] | None = None,
    ) -> tuple[list[M], int | None]:
        """Read distinct records with pagination and stable ordering."""
        if (page is None) != (items_per_page is None):
            raise InvalidInputError("Provide both page and items_per_page.")
        if page is not None and items_per_page is not None:
            if page < 1 or items_per_page < 1:
                raise InvalidInputError("Pagination values must be positive.")
        query = build_read_query(
            self.table_model,
            join_parameters,
            second_level_join_parameters,
        )
        query = apply_sorting(query, self.table_model, order_by, direction)
        count = None
        async with database_operation(db):
            if page is not None and items_per_page is not None:
                query = (
                    query.order_by(self.identity.attribute)
                    .offset(
                        (page - 1) * items_per_page,
                    )
                    .limit(items_per_page)
                )
                count = await db.scalar(
                    select(func.count()).select_from(self.table_model)
                )
            result = await db.execute(query)
            return list(result.unique().scalars().all()), count

    async def read_one(
        self,
        req_id: str,
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> M:
        """Read a single record and requested relationships by primary key."""
        identifier = self.identity.parse(req_id)
        query = (
            build_read_query(
                self.table_model,
                join_parameters,
                second_level_join_parameters,
            )
            .where(self.identity.attribute == identifier)
            .execution_options(populate_existing=True)
        )
        async with database_operation(db):
            result = await db.execute(query)
            record = result.unique().scalars().first()
        if record is None:
            raise ItemNotFoundError("Item not found.")
        return record

    async def create(
        self,
        body: BaseModel | dict[str, Any],
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> M:
        """Create one record, then load committed values and relationships."""
        if isinstance(body, BaseModel):
            values = body.model_dump()
        elif isinstance(body, dict):
            values = body
        else:
            raise InvalidInputError("Creation requires a single object.")
        record = self.table_model(**values)
        async with database_operation(db):
            db.add(record)
            await db.flush()
            identifier = str(self.identity.value(record))
            await db.commit()
            return await self.read_one(
                identifier,
                db,
                join_parameters,
                second_level_join_parameters,
            )

    async def update(
        self,
        req_id: str,
        body: dict[str, Any],
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> M:
        """Update mapped scalar columns, preserving the primary key."""
        columns = inspect(self.table_model).column_attrs
        if any(key not in columns for key in body):
            raise InvalidInputError("Only mapped columns can be updated.")
        async with database_operation(db):
            record = await self.read_one(req_id, db)
            for key, value in body.items():
                if key != self.identity.name:
                    setattr(record, key, value)
            await db.commit()
            return await self.read_one(
                req_id,
                db,
                join_parameters,
                second_level_join_parameters,
            )

    async def delete(self, req_id: str, db: AsyncSession) -> str:
        """Delete one record and preserve database foreign-key constraints."""
        identifier = self.identity.parse(req_id)
        query = delete(self.table_model).where(
            self.identity.attribute == identifier
        )
        async with database_operation(db):
            result = await db.execute(query)
            if result.rowcount == 0:
                raise ItemNotFoundError("Item not found.")
            await db.commit()
        return "Item deleted"
