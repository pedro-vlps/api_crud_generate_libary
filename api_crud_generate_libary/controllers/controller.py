"""Adapt CRUD request schemas and persistence results for HTTP routes."""

from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api_crud_generate_libary.controllers.http_errors import execute_http
from api_crud_generate_libary.queries.read_query import (
    JoinParameters,
    SecondLevelJoinParameters,
)
from api_crud_generate_libary.schemas.partial_schema import (
    create_partial_schema,
)
from api_crud_generate_libary.schemas.pattern_schema import (
    PatternSchemaDataList,
)
from api_crud_generate_libary.services.service import Service


class Controller:
    """Validate request contracts and delegate record operations."""

    def __init__(
        self,
        model_class: type,
        standard_schema: type[BaseModel],
        request_post_schema: type[BaseModel] | None = None,
        request_patch_schema: type[BaseModel] | None = None,
    ):
        self.service = Service(model_class)
        self.request_post_schema = request_post_schema or standard_schema
        self.request_patch_schema = (
            request_patch_schema or create_partial_schema(standard_schema)
        )

    async def get(
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
    ) -> PatternSchemaDataList:
        """Return a listing with metadata only when pagination is requested."""
        data, count = await execute_http(
            self.service.read(
                db,
                join_parameters,
                second_level_join_parameters,
                page,
                items_per_page,
                order_by,
                direction,
            )
        )
        payload = {"data": data}
        if page is not None and items_per_page is not None:
            payload.update(
                total_count=count, has_more=count > page * items_per_page
            )
        return PatternSchemaDataList(**payload)

    async def get_by_id(
        self,
        req_id: str,
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> dict[str, Any]:
        """Return a record in the standard response envelope."""
        data = await execute_http(
            self.service.read_one(
                req_id,
                db,
                join_parameters,
                second_level_join_parameters,
            )
        )
        return {"data": data}

    async def create(
        self,
        body: Any,
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> dict[str, Any]:
        """Validate a single input object before persisting it."""
        try:
            validated = self.request_post_schema.model_validate(body)
        except ValidationError as error:
            raise HTTPException(
                status_code=422,
                detail=jsonable_encoder(error.errors()),
            ) from error
        data = await execute_http(
            self.service.create(
                validated,
                db,
                join_parameters,
                second_level_join_parameters,
            )
        )
        return {"data": data}

    async def update(
        self,
        req_id: str,
        body: Any,
        db: AsyncSession,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ) -> dict[str, Any]:
        """Preserve omitted PATCH fields and validate explicit values."""
        try:
            validated = self.request_patch_schema.model_validate(body)
        except ValidationError as error:
            raise HTTPException(
                status_code=422,
                detail=jsonable_encoder(error.errors()),
            ) from error
        data = await execute_http(
            self.service.update(
                req_id,
                validated.model_dump(exclude_unset=True),
                db,
                join_parameters,
                second_level_join_parameters,
            )
        )
        return {"data": data}

    async def delete(self, req_id: str, db: AsyncSession) -> str:
        """Delete a record, translating expected failures into HTTP errors."""
        return await execute_http(self.service.delete(req_id, db))
