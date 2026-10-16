"""Compose typed FastAPI CRUD routes for a PostgreSQL model."""

from collections.abc import AsyncGenerator, Callable, Sequence
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api_crud_generate_libary.controllers.controller import Controller
from api_crud_generate_libary.queries.read_query import (
    JoinParameters,
    SecondLevelJoinParameters,
)
from api_crud_generate_libary.schemas.pattern_schema import (
    PatternSchema,
    PatternSchemaDataList,
)

S = TypeVar("S", bound=BaseModel)
M = TypeVar("M")


class Router(Generic[S, M]):
    """Compose typed CRUD operations and expose their FastAPI router."""

    def __init__(
        self,
        model_class: type[M],
        standard_schema: type[S],
        db_session: Callable[..., AsyncGenerator[AsyncSession, None]],
        request_post_schema: type[BaseModel] | None = None,
        request_patch_schema: type[BaseModel] | None = None,
        response_get_schema: type[BaseModel] | None = None,
        response_get_by_id_schema: type[BaseModel] | None = None,
        response_post_schema: type[BaseModel] | None = None,
        response_delete_schema: type[BaseModel] | None = None,
        response_patch_schema: type[BaseModel] | None = None,
        use_get: bool = True,
        use_get_by_id: bool = True,
        use_post: bool = True,
        use_delete: bool = True,
        use_patch: bool = True,
        auth_callback: (
            Sequence[Callable[..., Any]] | Callable[..., Any] | None
        ) = None,
        join_parameters: list[JoinParameters] | None = None,
        second_level_join_parameters: (
            list[SecondLevelJoinParameters] | None
        ) = None,
    ):
        self.standard_schema = standard_schema
        self.model_class = model_class
        self.db_session = db_session
        self.response_get_schema = response_get_schema or standard_schema
        self.response_get_by_id_schema = (
            response_get_by_id_schema or standard_schema
        )
        self.response_post_schema = response_post_schema or standard_schema
        self.response_delete_schema = response_delete_schema
        self.response_patch_schema = response_patch_schema or standard_schema
        callbacks = (
            [auth_callback]
            if callable(auth_callback)
            else (auth_callback or [])
        )
        self.auth_callback = list(callbacks)
        self.dependencies = [
            Depends(callback) for callback in self.auth_callback
        ]
        self.join_parameters = join_parameters
        self.second_level_join_parameters = second_level_join_parameters
        self.controller = Controller(
            model_class,
            standard_schema,
            request_post_schema,
            request_patch_schema,
        )
        self.request_post_schema = self.controller.request_post_schema
        self.request_patch_schema = self.controller.request_patch_schema
        self.router = APIRouter()
        for enabled, register in (
            (use_get, self.get_route),
            (use_get_by_id, self.get_id_route),
            (use_post, self.post_route),
            (use_delete, self.delete_route),
            (use_patch, self.patch_route),
        ):
            if enabled:
                register()

    def get_schema_example(self, schema: type[BaseModel] | None = None) -> Any:
        """Return an optional example; valid schemas never require one."""
        if schema is None:
            return None
        extra = schema.model_config.get("json_schema_extra")
        return extra.get("example") if isinstance(extra, dict) else None

    def get_route(self) -> None:
        """Register a listing with optional pagination and sorting."""

        async def get(
            db: AsyncSession = Depends(self.db_session),
            page: int | None = Query(None, ge=1),
            items_per_page: int | None = Query(None, gt=0),
            order_by: list[str] | None = Query(None),
            direction: list[str] | None = Query(None),
        ) -> Any:
            return await self.controller.get(
                db,
                self.join_parameters,
                self.second_level_join_parameters,
                page,
                items_per_page,
                order_by,
                direction,
            )

        self.router.add_api_route(
            "",
            get,
            methods=["GET"],
            response_model=PatternSchemaDataList[self.response_get_schema],
            response_model_exclude_unset=True,
            dependencies=self.dependencies,
        )

    def get_id_route(self) -> None:
        """Register lookup by the mapped primary key."""

        async def get_by_id(
            id_: str,
            db: AsyncSession = Depends(self.db_session),
        ) -> Any:
            return await self.controller.get_by_id(
                id_,
                db,
                self.join_parameters,
                self.second_level_join_parameters,
            )

        self.router.add_api_route(
            "/{id_}",
            get_by_id,
            methods=["GET"],
            response_model=PatternSchema[self.response_get_by_id_schema],
            dependencies=self.dependencies,
        )

    def post_route(self) -> None:
        """Create exactly one record per request."""

        async def post(
            body: Any = Body(...),
            db: AsyncSession = Depends(self.db_session),
        ) -> Any:
            return await self.controller.create(
                body,
                db,
                self.join_parameters,
                self.second_level_join_parameters,
            )

        # FastAPI inspects concrete annotations during route registration.
        post.__annotations__["body"] = self.request_post_schema
        self.router.add_api_route(
            "",
            post,
            methods=["POST"],
            response_model=PatternSchema[self.response_post_schema],
            response_model_exclude_unset=True,
            dependencies=self.dependencies,
        )

    def patch_route(self) -> None:
        """Register partial updates using the concrete input schema."""

        async def patch(
            id_: str,
            body: Any = Body(...),
            db: AsyncSession = Depends(self.db_session),
        ) -> Any:
            return await self.controller.update(
                id_,
                body,
                db,
                self.join_parameters,
                self.second_level_join_parameters,
            )

        patch.__annotations__["body"] = self.request_patch_schema
        self.router.add_api_route(
            "/{id_}",
            patch,
            methods=["PATCH"],
            response_model=PatternSchema[self.response_patch_schema],
            dependencies=self.dependencies,
        )

    def delete_route(self) -> None:
        """Keep the string response unless a message schema is configured."""

        async def delete(
            id_: str,
            db: AsyncSession = Depends(self.db_session),
        ) -> Any:
            message = await self.controller.delete(id_, db)
            if self.response_delete_schema:
                return self.response_delete_schema.model_validate(
                    {"message": message}
                )
            return message

        self.router.add_api_route(
            "/{id_}",
            delete,
            methods=["DELETE"],
            response_model=self.response_delete_schema or str,
            dependencies=self.dependencies,
        )
