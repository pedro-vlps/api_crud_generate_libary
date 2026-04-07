"""Generic SQL controller for CRUD operations file."""
from typing import Optional
from pydantic import ValidationError
from fastapi import HTTPException

from src.services.service import Service
from src.schemas.pattern_schema import PatternGetSchema

class Controller:
    """
        Controller for handling SQL operations.
        Provides methods for CRUD operations using 
        and setting up all parameters fot Service.
    """

    def __init__(
            self,
            model_class,
            standard_schema,
            request_post_schema,
            request_patch_schema
        ):
        self.model_class = model_class
        self.standard_schema = standard_schema
        self.service = Service(model_class)
        self.request_post_schema = request_post_schema
        self.request_patch_schema = request_patch_schema

    async def get(
        self,
        db,
        join_parameters: Optional[list] = None,
        second_level_join_parameters: Optional[list] = None,
        page: Optional[int] = None,
        items_per_page: Optional[int] = None,
        order_by: Optional[list[str]] = None,
        direction: Optional[list[str]] = None
    ):
        """Get all items from the database."""

        if (
            page is None and items_per_page is not None
        ) | (
            page is not None and items_per_page is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid pagination values"
            )

        response = await self.service.read(
            db,
            join_parameters,
            second_level_join_parameters,
            page,
            items_per_page,
            order_by,
            direction
        )

        payload = {
            "data": response[0]
        }

        if page is not None and items_per_page is not None:
            payload.update({
                "total_count": response[1],
                "has_more": response[1] > (page * items_per_page)
            })

        return PatternGetSchema(**payload)

    async def get_by_id(
        self,
        req_id,
        db,
        join_parameters: Optional[list] = None,
        second_level_join_parameters: Optional[list] = None
    ):
        """Get a single item by ID from the database."""

        response = await self.service.read_one(
            req_id,
            db,
            join_parameters,
            second_level_join_parameters
        )
        return {
            "data": response,
        }

    async def create(
        self,
        body,
        db,
        join_parameters,
        second_level_join_parameters
    ):
        """Create a new item in the database."""
        try:
            if self.request_post_schema:
                if isinstance(body, list):
                    validated_body = [
                        self.request_post_schema.model_validate(item)
                        for item in body
                    ]
                else:
                    validated_body = self.request_post_schema.model_validate(
                        body
                    )
            else:
                if isinstance(body, list):
                    validated_body = [
                        self.standard_schema.model_validate(item)
                        for item in body
                    ]
                else:
                    validated_body = self.standard_schema.model_validate(body)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors()) from e

        response = await self.service.create(
            validated_body,
            db,
            join_parameters,
            second_level_join_parameters
        )
        return {
            "data": response,
        }

    async def delete(
        self,
        req_id,
        db
    ):
        """Delete an item by ID from the database."""

        response = await self.service.delete(req_id, db)
        return response

    async def update(
        self,
        req_id,
        body,
        db,
        join_parameters,
        second_level_join_parameters
    ):
        """Update an existing item in the database."""
        try:
            if self.request_patch_schema:
                validated_body = self.request_patch_schema.model_validate(body)
            else:
                validated_body = self.standard_schema.model_validate(body)

            validated_body = validated_body.model_dump(exclude_unset=True)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors()) from e

        response = await self.service.update(
            req_id,
            validated_body,
            db,
            join_parameters,
            second_level_join_parameters
        )
        return {
            "data": response,
        }
