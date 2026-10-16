"""Check validation, OpenAPI and authentication without a running database."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field, ValidationError

from api_crud_generate_libary import MessageSchema, Router
from api_crud_generate_libary.schemas.partial_schema import (
    create_partial_schema,
)
from tests.models import Item, ItemRequest


async def unused_session():
    """HTTP contract tests replace persistence with an explicit mock."""
    yield None


def application(**options):
    """Compose an app while retaining the router for behavior assertions."""
    router = Router(Item, ItemRequest, unused_session, **options)
    app = FastAPI()
    app.include_router(router.router, prefix="/items")
    return app, router


def resolve_schema(document, schema):
    """Follow a JSON Schema reference in the generated OpenAPI document."""
    if "$ref" in schema:
        return document["components"]["schemas"][
            schema["$ref"].rsplit("/", 1)[-1]
        ]
    return schema


def test_schema_without_example_and_concrete_openapi():
    """Ordinary schemas initialize, and request bodies advertise real fields."""
    app, _ = application()
    document = app.openapi()
    for method, path in (("post", "/items"), ("patch", "/items/{id_}")):
        body = document["paths"][path][method]["requestBody"]
        schema = resolve_schema(
            document, body["content"]["application/json"]["schema"]
        )
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "anyOf" not in schema
        if method == "patch":
            assert "required" not in schema


@pytest.mark.parametrize(
    "body", [[], [{"name": "one", "description": "first"}]]
)
async def test_post_rejects_lists(body):
    """Reject POST lists before reaching persistence."""
    app, router = application()
    router.controller.service.create = AsyncMock()
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post("/items", json=body)
    assert response.status_code == 422
    router.controller.service.create.assert_not_awaited()


async def test_patch_preserves_omitted_fields():
    """The generated PATCH schema sends only fields present in the request."""
    app, router = application()
    router.controller.service.update = AsyncMock(
        return_value={"name": "changed", "description": "original"},
    )
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/items/{uuid4()}", json={"name": "changed"}
        )
    assert response.status_code == 200
    assert router.controller.service.update.await_args.args[1] == {
        "name": "changed"
    }


async def test_custom_patch_contract_is_respected():
    """An explicit input schema retains its required fields and constraints."""

    class PatchRequest(BaseModel):
        """A deliberately required custom PATCH field."""

        name: str = Field(min_length=3)

    app, router = application(request_patch_schema=PatchRequest)
    router.controller.service.update = AsyncMock()
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.patch(f"/items/{uuid4()}", json={})
    assert response.status_code == 422
    router.controller.service.update.assert_not_awaited()


def test_partial_schema_preserves_nullability_and_constraints():
    """Omission does not authorize invalid explicit null or short values."""
    partial = create_partial_schema(ItemRequest)
    assert partial.model_validate({}).model_dump(exclude_unset=True) == {}
    for body in ({"name": None}, {"name": ""}):
        with pytest.raises(ValidationError):
            partial.model_validate(body)
    assert partial.model_validate({"category_key": None}).category_key is None


@pytest.mark.parametrize("custom_schema", [None, MessageSchema])
async def test_delete_contract(custom_schema):
    """Preserve the historical string, or honor the configured message model."""
    app, router = application(response_delete_schema=custom_schema)
    router.controller.service.delete = AsyncMock(return_value="Item deleted")
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/items/{uuid4()}")
    assert response.status_code == 200
    expected = {"message": "Item deleted"} if custom_schema else "Item deleted"
    assert response.json() == expected


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/items", None),
        ("GET", "/items/550e8400-e29b-41d4-a716-446655440000", None),
        ("POST", "/items", {"name": "item", "description": "description"}),
        (
            "PATCH",
            "/items/550e8400-e29b-41d4-a716-446655440000",
            {"name": "item"},
        ),
        ("DELETE", "/items/550e8400-e29b-41d4-a716-446655440000", None),
    ],
)
async def test_authentication_applies_to_every_route(method, path, body):
    """Apply authentication consistently to every operation."""

    async def deny():
        raise HTTPException(status_code=401, detail="Authentication required")

    app, _ = application(auth_callback=[deny])
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.request(method, path, json=body)
    assert response.status_code == 401


def test_route_flags():
    """Disabled operations are absent from the router."""
    app, _ = application(
        use_get=False,
        use_get_by_id=False,
        use_post=False,
        use_patch=False,
    )
    assert set(app.openapi()["paths"]) == {"/items/{id_}"}
    assert set(app.openapi()["paths"]["/items/{id_}"]) == {"delete"}
