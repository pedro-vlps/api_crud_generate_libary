"""Generic SQL service for CRUD operations file."""
from uuid import UUID
from typing import Generic, TypeVar, Type, Any, Optional
from fastapi import HTTPException
from sqlalchemy import select, delete, func, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError, DBAPIError
from asyncpg.exceptions import UniqueViolationError, StringDataRightTruncationError  # type: ignore

from api_crud_generate_libary.helpers.join_load_builder import build_joinedload_chain  # type: ignore

M = TypeVar("M")

class Service(Generic[M]):
    """Generic service for SQL operations."""
    def __init__(self, table_model: Type[M]):
        self.table_model = table_model

    async def read(
        self,
        db: Any,
        join_parameters: Optional[list[dict[str, Any]]],
        second_level_join_parameters: Optional[list[dict[str, Any]]],
        page: Optional[int],
        items_per_page: Optional[int],
        order_by: Optional[list[str]],
        direction: Optional[list[str]]
    ) -> Any:
        """Set the query and crete the session to read all items"""

        async with db as session:
            query = select(self.table_model)
            query_parameters = []

            try:
                if join_parameters:
                    for join in join_parameters:
                        query = query.outerjoin(
                            join["model"],
                            getattr(
                                self.table_model, join["column"]
                            ) == getattr(
                                join["model"], "id"
                            )
                        )

                        query = query.options(
                            joinedload(
                                join["response_parameter"]
                            )
                        )

                if second_level_join_parameters:
                    for join in second_level_join_parameters:
                        query = query.outerjoin(
                            join["second_model"],
                            getattr(
                                join["first_model"], join["column"]
                            ) == getattr(
                                join["second_model"], "id"
                            )
                        )

                        loads = build_joinedload_chain(
                            join["response_parameter"]
                        )
                        query = query.options(
                            loads
                        )

                    query = query.where(
                        or_(
                            *query_parameters  # type: ignore
                        )
                    )

                if (
                    order_by is not None and
                    direction is not None and
                    len(order_by) == len(direction)
                ):
                    for index, column in enumerate(order_by):
                        if direction[index].lower() == "asc":
                            query = query.order_by(
                                getattr(self.table_model, column).asc()
                            )
                        elif direction[index].lower() == "desc":
                            query = query.order_by(
                                getattr(self.table_model, column).desc()
                            )
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail=(
                                    "Invalid order direction. "
                                    "Use 'asc' or 'desc'."
                                )
                            )
            except AttributeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid order_by field: {order_by}"
                        f" or join_parameters: {join_parameters}"
                    )
                ) from e

            if page is not None and items_per_page is not None:
                query = query.offset(
                    (page-1) * items_per_page
                ).limit(
                    items_per_page
                )

            count_query = select(
                func.count() #pylint: disable=E1102
            ).select_from(
                self.table_model
            )

            count_result = await session.execute(count_query)
            count = count_result.scalar()

            result = await session.execute(query)
            data = result.scalars().all()

            return [
                data, count
            ] if page is not None and items_per_page is not None else [
                data, None
            ]


    async def read_one(
        self,
        req_id: str,
        db: Any,
        join_parameters: Optional[list[dict[str, Any]]],
        second_level_join_parameters: Optional[list[dict[str, Any]]]
    ) -> Any:
        """
            Set the query, check the UUID sent
            and crete the session to read one item by ID
        """
        try:
            uuid_id = UUID(req_id)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Incorrect Id format"
            ) from e

        async with db as session:
            query = select(
                self.table_model
            )

            if join_parameters:
                for join in join_parameters:
                    query = query.outerjoin(
                        join["model"],
                        getattr(
                            self.table_model, join["column"]
                        ) == getattr(
                            join["model"], "id"
                        )
                    )

                    query = query.options(
                        joinedload(
                            join["response_parameter"]
                        )
                    )

            if second_level_join_parameters:
                for join in second_level_join_parameters:
                    query = query.outerjoin(
                        join["second_model"],
                        getattr(
                            join["first_model"], join["column"]
                        ) == getattr(
                            join["second_model"], "id"
                        )
                    )

                    loads = build_joinedload_chain(join["response_parameter"])
                    query = query.options(
                        loads
                    )

            query = query.where(self.table_model.id == uuid_id)  # type: ignore

            result = await session.execute(query)
            data = result.scalars().first()

            if data:
                return data
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Not found item"
                )

    async def create(
        self,
        body: Any,
        db: Any,
        join_parameters: Optional[list[dict[str, Any]]] = None,
        second_level_join_parameters: Optional[list[dict[str, Any]]] = None
    ) -> Any:
        """
            Check the request body, create the session,
            Create a new item in the database and validate
            the database response.
        """
        try:
            if hasattr(body, "dict"):
                body = body.dict()

            new_item = self.table_model(**body)

            db.add(new_item)
            await db.commit()

            if join_parameters is None:
                return new_item
            else:
                return await self.read_one(
                    str(new_item.id),  # type: ignore
                    db,
                    join_parameters,
                    second_level_join_parameters
                )

        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail=(
                    "Unable to create item "
                    "because it does not comply with business rules."
                )
            ) from e
        except UniqueViolationError as e:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail=(
                    "Unable to create the item because "
                    "should be a unique key value."
                )
            ) from e
        except (StringDataRightTruncationError, DBAPIError) as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unable to create the item because "
                    "item length is incorrect."
                )
            ) from e

    async def delete(self, req_id: str, db: Any) -> str:
        """
            Check the UUID sent, Delete an item by ID from
            database and validate the database response.
        """
        async with db as session:
            try:
                uuid_obj = UUID(req_id)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail="Incorrect Id format"
                ) from e

            query = delete(
                self.table_model
            ).where(self.table_model.id == uuid_obj)  # type: ignore

            try:
                result = await session.execute(query)

                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Not found item"
                    )

                await session.commit()
            except IntegrityError as e:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Unable to delete the item because "
                        "it is being referenced by another table."
                    )
                ) from e

            return "Item deleted"

    async def update(
        self,
        req_id: str,
        body: dict[str, Any],
        db: Any,
        join_parameters: Optional[list[dict[str, Any]]] = None,
        second_level_join_parameters: Optional[list[dict[str, Any]]] = None
    ) -> Any:
        """
            Check the request body, check the UUID sent,
            Update an existing item in the database and
            validate the database response.
        """
        try:
            uuid_id = UUID(req_id)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Incorrect Id format"
            ) from e

        async with db as session:
            query = select(
                self.table_model
            ).where(self.table_model.id == uuid_id)  # type: ignore
            result = await session.execute(query)
            data = result.scalars().first()

            if data:
                for key, value in body.items():
                    if key != "id":
                        setattr(data, key, value)

                try:
                    await session.commit()
                    await session.refresh(data)

                    if join_parameters is None:
                        return data
                    else:
                        return await self.read_one(
                            req_id,
                            db,
                            join_parameters,
                            second_level_join_parameters
                        )

                except (IntegrityError, UniqueViolationError) as e:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Unable to update the item because "
                            "should be a unique key value."
                        )
                    ) from e
                except (StringDataRightTruncationError, DBAPIError) as e:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Unable to update the item because "
                            "field length is incorrect."
                        )
                    ) from e
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Not found item"
                )
