"""Exercise real PostgreSQL persistence, constraints and eager relationships."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from api_crud_generate_libary import Router
from api_crud_generate_libary.errors import (
    ConstraintConflictError,
    InvalidDataError,
    InvalidInputError,
    ItemNotFoundError,
)
from api_crud_generate_libary.services.service import Service
from tests.models import (
    Category,
    CategoryWithItems,
    CategoryWithNestedItems,
    Item,
    ItemRequest,
    ItemResponse,
    ItemWithCategory,
    StringRecord,
)

pytestmark = pytest.mark.postgresql


async def test_crud_with_default_session_expiration(sessions):
    """Committed records serialize and the caller can keep using the session."""
    service = Service(Item)
    async with sessions() as session:
        created = await service.create(
            {"name": "first", "description": "original"}, session
        )
        identifier = str(created.id)
        assert ItemResponse.model_validate(created).description == "original"
        records, count = await service.read(session, page=1, items_per_page=1)
        assert len(records) == count == 1
        updated = await service.update(identifier, {"name": "changed"}, session)
        assert ItemResponse.model_validate(updated).description == "original"
        assert await session.scalar(select(func.count()).select_from(Item)) == 1
        assert await service.delete(identifier, session) == "Item deleted"
        with pytest.raises(ItemNotFoundError):
            await service.read_one(identifier, session)


async def test_constraints_rollback_and_session_reuse(sessions):
    """Unique, length and foreign-key failures have distinct safe errors."""
    service = Service(Item)
    async with sessions() as session:
        await service.create({"name": "unique"}, session)
        with pytest.raises(ConstraintConflictError):
            await service.create({"name": "unique"}, session)
        with pytest.raises(InvalidDataError):
            await service.create({"name": "x" * 21}, session)
        with pytest.raises(ConstraintConflictError):
            await service.create(
                {"name": "missing parent", "category_key": 999}, session
            )
        created = await service.create({"name": "recovered"}, session)
        assert created.description == "default description"


async def test_failed_update_rolls_back(sessions):
    """After a conflict, a later operation succeeds on the same session."""
    service = Service(Item)
    async with sessions() as session:
        first = await service.create({"name": "first"}, session)
        identifier = str(first.id)
        await service.create({"name": "second"}, session)
        with pytest.raises(ConstraintConflictError):
            await service.update(identifier, {"name": "second"}, session)
        recovered = await service.update(
            identifier, {"description": "recovered"}, session
        )
        assert recovered.name == "first"


async def test_integer_and_string_primary_keys(sessions):
    """Identifiers are parsed from the actual mapped key, including its name."""
    async with sessions() as session:
        category_service = Service(Category)
        category = await category_service.create({"name": "category"}, session)
        key = str(category.category_key)
        assert (
            await category_service.read_one(key, session)
        ).name == "category"
        assert (
            await category_service.update(key, {"name": "renamed"}, session)
        ).name == "renamed"
        with pytest.raises(InvalidInputError):
            await category_service.read_one("invalid", session)
        await category_service.delete(key, session)
        string_service = Service(StringRecord)
        await string_service.create(
            {"code": "sku-1", "name": "record"}, session
        )
        assert (
            await string_service.read_one("sku-1", session)
        ).name == "record"
        await string_service.delete("sku-1", session)


async def test_relationships_and_collection_pagination(sessions):
    """Preserve root records and page boundaries with joined collections."""
    async with sessions() as session:
        category = await Service(Category).create({"name": "parent"}, session)
        key = category.category_key
        item_service = Service(Item)
        joins = [{"response_parameter": Item.category}]
        first = await item_service.create(
            {"name": "first", "category_key": key},
            session,
            joins,
        )
        first_id = str(first.id)
        assert ItemWithCategory.model_validate(first).category.name == "parent"
        await item_service.create(
            {"name": "second", "category_key": key}, session
        )
        updated = await item_service.update(
            first_id,
            {"description": "joined"},
            session,
            joins,
        )
        assert ItemWithCategory.model_validate(updated).description == "joined"
        category_service = Service(Category)
        records, count = await category_service.read(
            session,
            [{"response_parameter": Category.items}],
            page=1,
            items_per_page=1,
        )
        assert count == 1 and len(records) == 1
        assert len(CategoryWithItems.model_validate(records[0]).items) == 2
        nested = [{"response_parameter": [Category.items, Item.category]}]
        parent = await category_service.read_one(
            str(key), session, None, nested
        )
        assert len(CategoryWithNestedItems.model_validate(parent).items) == 2
        with pytest.raises(ConstraintConflictError):
            await category_service.delete(str(key), session)
        assert (
            await session.scalar(select(func.count()).select_from(Category))
            == 1
        )


@pytest.mark.parametrize(
    "arguments",
    [
        {"page": 1},
        {"items_per_page": 1},
        {"page": 0, "items_per_page": 1},
        {"order_by": ["name"]},
        {"order_by": ["name"], "direction": ["invalid"]},
        {"order_by": ["__dict__"], "direction": ["asc"]},
        {"order_by": ["name"], "direction": ["asc", "desc"]},
    ],
)
async def test_invalid_queries(sessions, arguments):
    """Malformed sorting and pagination are rejected predictably."""
    async with sessions() as session:
        with pytest.raises(InvalidInputError):
            await Service(Item).read(session, **arguments)


async def test_http_crud_round_trip(sessions):
    """The complete API supports single POST, partial PATCH and safe errors."""

    async def database_session():
        async with sessions() as session:
            yield session

    router = Router(
        Item,
        ItemRequest,
        database_session,
        response_get_schema=ItemResponse,
        response_get_by_id_schema=ItemResponse,
        response_post_schema=ItemResponse,
        response_patch_schema=ItemResponse,
    )
    app = FastAPI()
    app.include_router(router.router, prefix="/items")
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/items", json={"name": "item", "description": "original"}
        )
        assert response.status_code == 200
        identifier = response.json()["data"]["id"]
        response = await client.patch(
            f"/items/{identifier}", json={"name": "renamed"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["description"] == "original"
        response = await client.get(
            "/items", params={"page": 1, "items_per_page": 1}
        )
        assert response.json()["total_count"] == 1
        assert response.json()["has_more"] is False
        assert (await client.get(f"/items/{identifier}")).status_code == 200
        response = await client.post(
            "/items", json={"name": "renamed", "description": "duplicate"}
        )
        assert response.status_code == 409
        assert "INSERT" not in response.text
        assert (await client.get("/items/not-a-uuid")).status_code == 400
        assert (await client.get(f"/items/{uuid4()}")).status_code == 404
        assert (
            await client.delete(f"/items/{identifier}")
        ).json() == "Item deleted"
