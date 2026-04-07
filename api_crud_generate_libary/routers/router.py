"""Generic Router file for API endpoints."""
from typing import Generic, TypeVar, Type, AsyncGenerator, Optional, Callable, Union, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Body, Query
from api_crud_generate_libary.controllers.controller import Controller
from api_crud_generate_libary.schemas.pattern_schema import PatternSchema, PatternGetSchema, PatternSchemaDataList

# Type variables for generic types.
S = TypeVar("S")
M = TypeVar("M")

REQP = TypeVar("REQP", bound=S) # type: ignore
REQU = TypeVar("REQU", bound=S) # type: ignore

RESG = TypeVar("RESG", bound=S) # type: ignore
RESGID = TypeVar("RESGID", bound=S) # type: ignore
RESP = TypeVar("RESP", bound=S) # type: ignore
RESD = TypeVar("RESD", bound=S) # type: ignore
RESU = TypeVar("RESU", bound=S) # type: ignore

class SqlRouter(Generic[S, M]):
    """
        Router class for handling SQL operations with FastAPI.

        Initialize the SQL Router with necessary parameters.
    """
    def __init__(
            self,
            model_class: Type[M],
            standard_schema: Type[S],
            db_session: Callable[[], AsyncGenerator[AsyncSession, None]],
            request_post_schema: Optional[Type[REQP]] = None,
            request_patch_schema: Optional[Type[REQU]] = None,
            response_get_schema: Optional[Type[RESG]] = None,
            response_get_by_id_schema: Optional[Type[RESGID]] = None,
            response_post_schema: Optional[Type[RESP]] = None,
            response_delete_schema: Optional[Type[RESD]] = None,
            response_patch_schema: Optional[Type[RESU]] = None,
            use_get: Optional[bool] = True,
            use_get_by_id: Optional[bool] = True,
            use_post: Optional[bool] = True,
            use_delete: Optional[bool] = True,
            use_patch: Optional[bool] = True,
            auth_callback: Optional[Callable[..., Any]] = None,
            join_parameters: Optional[list[Any]] = None,
            second_level_join_parameters: Optional[list[Any]] = None,
        ):
        self.standard_schema = standard_schema
        self.model_class = model_class
        self.db_session = db_session
        self.request_post_schema = request_post_schema
        self.request_patch_schema = request_patch_schema
        self.response_get_schema = response_get_schema
        self.response_get_by_id_schema = response_get_by_id_schema
        self.response_post_schema = response_post_schema
        self.response_delete_schema = response_delete_schema
        self.response_patch_schema = response_patch_schema
        self.router = APIRouter()
        self.controller = Controller(
            model_class= model_class,
            standard_schema=standard_schema,
            request_post_schema=request_post_schema,
            request_patch_schema=request_patch_schema,
        )
        self.auth_callback = auth_callback
        self.join_parameters = join_parameters
        self.second_level_join_parameters = second_level_join_parameters

        """Register routes based on the provided flags"""

        if use_get:
            self.get_route()

        if use_get_by_id:
            self.get_id_route()

        if use_post:
            self.post_route()

        if use_delete:
            self.delete_route()

        if use_patch:
            self.patch_route()

    def get_schema_example(self, schema: Optional[Any] = None) -> dict[str, Any]:
        """Extract a schema example from model_config"""
        item = getattr(
            schema,
            "model_config",
            {}
        )

        return item["json_schema_extra"]["example"]

    def get_route(self):
        """
            Define the GET route

            get: Function from controller
                used by router to get all items
                filtering by a query string
            
            define_router: Route creation for getting
                all items filtering by a query string
        """
        schema = self.response_get_schema or self.standard_schema

        async def get(
            db: AsyncSession = Depends(self.db_session),
            page: Optional[int] = Query(None, ge=1),
            items_per_page: Optional[int] = Query(None, gt=0),
            order_by: Optional[list[str]] = Query(None),
            direction: Optional[list[str]] = Query(None)
        ) -> Any:
            response: Any = await self.controller.get(  # type: ignore
                db,
                self.join_parameters,
                self.second_level_join_parameters,
                page,
                items_per_page,
                order_by,
                direction
            )
            return response

        self.router.add_api_route(
            "",
            get,
            response_model=PatternGetSchema[schema],
            response_model_exclude_unset=True,
            methods=["GET"],
            dependencies=[
                Depends(self.auth_callback)
            ] if self.auth_callback else []
        )

    def get_id_route(self):
        """
            Define the GET by ID route

            get_by_id: Function from controller
                used by router to get an item by ID
            
            define_router: Route creation for
                getting a single item by ID
        """
        schema = self.response_get_by_id_schema or self.standard_schema

        async def get_by_id(
            id_: str,
            db: AsyncSession = Depends(self.db_session)
        ) -> Any:
            response: Any = await self.controller.get_by_id(  # type: ignore
                id_,
                db,
                self.join_parameters,
                self.second_level_join_parameters
            )
            return response

        self.router.add_api_route(
            "/{id_}",
            get_by_id,
            response_model=PatternSchema[schema],
            methods=["GET"],
            dependencies=[
                Depends(self.auth_callback)
            ] if self.auth_callback else []
        )

    def post_route(self):
        """
            Define the POST route

            post: Function from controller
                used by router to create an item
            
            define_router: Route creation for
                create a single item
        """
        input_schema = self.request_post_schema or self.standard_schema
        response_schema = self.response_post_schema or self.standard_schema

        async def post(
            body: Union[dict[str, Any], list[Any]] = Body(...),
            db: AsyncSession = Depends(self.db_session)
        ) -> Any:
            response: Any = await self.controller.create(  # type: ignore
                body,
                db,
                self.join_parameters,
                self.second_level_join_parameters
            )
            return response

        self.router.add_api_route(
            "",
            post,
            response_model=Union[
                PatternSchema[response_schema],
                PatternSchemaDataList[response_schema]
            ],
            methods=["POST"],
            dependencies=[
                Depends(self.auth_callback)
            ] if self.auth_callback else [],
            openapi_extra={
                "requestBody": {
                    "content": {
                        "application/json": {
                            "example": self.get_schema_example(
                                input_schema
                            )
                        }
                    }
                }
            }
        )

    def delete_route(self):
        """
            Define the DELETE route

            delete: Function from controller
                used by router to delete an item
            
            define_router: Route creation for
                delete a single item
        """

        async def delete(
            id_: str,
            db: AsyncSession = Depends(self.db_session)
        ) -> Any:
            response: Any = await self.controller.delete(id_, db)  # type: ignore
            return response

        self.router.add_api_route(
            "/{id_}",
            delete,
            methods=["DELETE"],
            status_code=204,
            dependencies=[
                Depends(self.auth_callback)
            ] if self.auth_callback else []
        )

    def patch_route(self):
        """
            Define the PATCH route

            patch: Function from controller
                used by router to update a table item(s)
            
            define_router: Route creation for
                update table item(s)
        """

        input_schema = self.request_patch_schema or self.standard_schema
        response_schema = self.response_patch_schema or self.standard_schema # pylint: disable=line-too-long

        async def patch(
            id_: str,
            body: S = Body(...),
            db: AsyncSession = Depends(self.db_session)
        ) -> Any:
            response: Any = await self.controller.update(  # type: ignore
                id_,
                body,
                db,
                self.join_parameters,
                self.second_level_join_parameters
            )
            return response

        self.router.add_api_route(
            "/{id_}",
            patch,
            response_model=PatternSchema[response_schema],
            methods=["PATCH"],
            dependencies=[
                Depends(self.auth_callback)
            ] if self.auth_callback else [],
            openapi_extra={
                "requestBody": {
                    "content": {
                        "application/json": {
                            "example": self.get_schema_example(
                                input_schema
                            )
                        }
                    }
                }
            }
        )
