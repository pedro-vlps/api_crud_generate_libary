"""Compose the example application and item routes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api_crud_generate_libary import Router
from examples.postgresql.database import database_session, engine
from examples.postgresql.models import Base, Item
from examples.postgresql.schemas import ItemCreate, ItemRead


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create demo tables; production applications should use migrations."""
    del application
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield
    finally:
        await engine.dispose()


app = FastAPI(lifespan=lifespan)
item_router = Router(
    model_class=Item,
    standard_schema=ItemCreate,
    db_session=database_session,
    response_get_schema=ItemRead,
    response_get_by_id_schema=ItemRead,
    response_post_schema=ItemRead,
    response_patch_schema=ItemRead,
)
app.include_router(item_router.router, prefix="/items", tags=["Items"])
