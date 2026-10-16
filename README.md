# CRUD Generator Library

Generate typed FastAPI CRUD routes from SQLAlchemy models and Pydantic schemas,
using **PostgreSQL with asyncpg**.

The library supplies listing, lookup, single-record creation, partial updates
and deletion. Your application supplies the database models, validation schemas,
session dependency and authentication dependencies.

- Python: **3.13 or later**.
- Database: **PostgreSQL only**.
- ORM: SQLAlchemy 2.x with async sessions.
- Validation: Pydantic 2.x.
- License: [MIT](LICENSE).
- Distribution name: `api-crud-generate-libary`.
- Python import: `api_crud_generate_libary`.

The original `libary` spelling is retained in package names for compatibility.

## Contents

1. [Requirements](#1-requirements)
2. [Installation](#2-installation)
3. [PostgreSQL setup](#3-postgresql-setup)
4. [Application structure](#4-application-structure)
5. [Database and session configuration](#5-database-and-session-configuration)
6. [SQLAlchemy models](#6-sqlalchemy-models)
7. [Pydantic schemas](#7-pydantic-schemas)
8. [CRUD router configuration](#8-crud-router-configuration)
9. [FastAPI startup](#9-fastapi-startup)
10. [Calling every endpoint](#10-calling-every-endpoint)
11. [Partial update behavior](#11-partial-update-behavior)
12. [Complete configuration reference](#12-complete-configuration-reference)
13. [Authentication](#13-authentication)
14. [Relationships](#14-relationships)
15. [Primary key alternatives](#15-primary-key-alternatives)
16. [Sessions, transactions and failures](#16-sessions-transactions-and-failures)
17. [Database migrations](#17-database-migrations)
18. [Existing runnable example](#18-existing-runnable-example)
19. [Contributor setup, tests and packaging](#19-contributor-setup-tests-and-packaging)
20. [Troubleshooting](#20-troubleshooting)
21. [License](#21-license)

## 1. Requirements

Install Python 3.13+ and a reachable PostgreSQL server. Git is only needed for
source installations or library development. Docker is optional: this guide
uses a container as one way to run a local database.

Uvicorn runs the example HTTP server. It is an application runtime dependency,
not a requirement for importing the library. Poetry is only required for the
contributor workflow in section 19.

Check the tools available in your terminal:

```bash
python --version
```

If your system exposes Python as `python3`, use that executable consistently.

## 2. Installation

### Recommended: install from PyPI after publication

After the package has been published on PyPI, applications can install it by
name. Git and a source checkout are not required for this method.

Create your application directory and virtual environment:

```bash
mkdir my_crud_api
cd my_crud_api
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Install the library and the example HTTP server:

```bash
python -m pip install --upgrade pip
python -m pip install api-crud-generate-libary uvicorn
python -m pip check
```

**Publication status:** the commands above describe installation after a PyPI
release. This repository update does not publish a release. Until that happens,
use the local-source or Git alternatives below. An unavailable PyPI release
cannot be installed by name.

FastAPI, Pydantic, `sqlalchemy[asyncio]` and `asyncpg` are installed automatically.
The SQLAlchemy `asyncio` extra includes `greenlet`.

Verify the installed version:

```bash
python -c "from api_crud_generate_libary import Router; from importlib.metadata import version; print(version('api-crud-generate-libary'))"
```

Continue with PostgreSQL setup and create `sample_app` inside `my_crud_api`.
The application code in the remaining sections is the same for PyPI and source
installations.

### Using Poetry for an application

Install Poetry first using its [official installation guide](https://python-poetry.org/docs/#installation).
Confirm that Poetry and a compatible Python interpreter are available:

```bash
poetry --version
python --version
```

For a new application, create a directory and initialize its dependency manifest:

```bash
mkdir my_crud_api
cd my_crud_api
poetry init --name my-crud-api --python ">=3.13,<4.0" --no-interaction
```

This produces `pyproject.toml`. Because the tutorial builds an application rather
than a distributable Python package, add this table to that file:

```toml
[tool.poetry]
package-mode = false
```

If the table already exists, add the setting to it rather than duplicating the
table. Existing projects that intentionally package their application can retain
their established package configuration.

Configure a project-local virtual environment and choose your Python interpreter:

```bash
poetry config virtualenvs.in-project true --local
poetry env use python
```

The selected interpreter must be Python 3.13 or later. If `python` points to a
different version, pass the compatible interpreter's executable or absolute path
to `poetry env use` instead.

After publication on PyPI, install the library and Uvicorn:

```bash
poetry add api-crud-generate-libary uvicorn
```

Before publication, use your local checkout instead, replacing the path:

```bash
poetry add /path/to/api_crud_generate_libary uvicorn
```

Run only the installation command appropriate to your source. Poetry updates
`pyproject.toml`, generates `poetry.lock`, and installs the dependencies. For an
existing application, skip project initialization and use `poetry add` inside
that application's directory.

Check the environment and the installed library:

```bash
poetry env info
poetry run python --version
poetry run python -c "from api_crud_generate_libary import Router; from importlib.metadata import version; print(version('api-crud-generate-libary'))"
```

Follow sections 3 through 9, creating `sample_app` at the same level as your
`pyproject.toml`. Set `DATABASE_URL` in the current terminal as shown in section
3. Poetry passes that environment variable to the application; a `.env` file is
not loaded automatically by this guide.

Start the application through Poetry:

```bash
poetry run python -m uvicorn sample_app.main:app --reload
```

You do not need to activate the virtual environment manually or use `poetry
shell`. When another developer checks out your application with its manifest
and lockfile, `poetry install` restores its dependencies. Keep path dependencies
reachable until you intentionally replace them with the published PyPI package.

### Alternative: install a local checkout

Use this method before publication, when testing local changes, or when
contributing to the library. Git is required to obtain a new checkout:

```bash
git clone https://github.com/pedro-vlps/api_crud_generate_libary.git
cd api_crud_generate_libary
python -m venv .venv
```

If you already have the checkout, enter it instead of cloning again. Activate
its environment using the platform-specific command above, then install:

```bash
python -m pip install --upgrade pip
python -m pip install -e . uvicorn
python -m pip check
```

Editable installation (`-e`) makes changes to this checkout immediately
available. For a fixed copy, use `python -m pip install . uvicorn`.

Select the branch or release containing the version you intend to run; unpushed
changes are available only in your local copy. You can create the guide's
`sample_app` at the checkout root.

To use a local checkout from another application's virtual environment:

```bash
python -m pip install /path/to/api_crud_generate_libary uvicorn
```

Replace the path with the actual checkout path and quote it if it contains
spaces. In an existing Poetry application, the equivalent is
`poetry add /path/to/api_crud_generate_libary uvicorn`.

### Alternative: install directly from Git

```bash
python -m pip install "git+https://github.com/pedro-vlps/api_crud_generate_libary.git"
```

This installs the remote default branch, not local unpushed changes. For a
reproducible Git installation, append `@COMMIT_OR_TAG` to the URL using a
published ref. Git is required for this installation method.

## 3. PostgreSQL setup

Use an existing empty development database, or start a local PostgreSQL 16
container. The following credentials are disposable examples:

```bash
docker run --name crud-postgres -e POSTGRES_USER=crud_user -e POSTGRES_PASSWORD=local_dev_password -e POSTGRES_DB=crud_demo -p 127.0.0.1:5432:5432 -d postgres:16
docker exec crud-postgres pg_isready -U crud_user -d crud_demo
```

Wait until the database accepts connections before starting the application.
On subsequent runs, use `docker start crud-postgres` rather than creating a
second container with the same name. This quick-start container has no named
volume; use an appropriate storage configuration for data you need to retain.

If port 5432 is occupied, publish another host port such as
`-p 127.0.0.1:5433:5432`, and use 5433 in the connection URL.

For an existing PostgreSQL installation, an administrator can create the
equivalent role and database through `psql`:

```sql
CREATE ROLE crud_user WITH LOGIN PASSWORD 'local_dev_password';
CREATE DATABASE crud_demo OWNER crud_user;
```

Choose one setup method; do not create the same role and database twice.

Set the URL in the terminal that will run the application.

Windows PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://crud_user:local_dev_password@127.0.0.1:5432/crud_demo"
```

Linux/macOS:

```bash
export DATABASE_URL='postgresql+asyncpg://crud_user:local_dev_password@127.0.0.1:5432/crud_demo'
```

The connection format is:

```text
postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

The `+asyncpg` driver is required. Percent-encode reserved URL characters in a
username or password. This guide reads environment variables directly; creating
a `.env` file alone does not load its values.

Keep real credentials outside source files and Git. In a containerized
application, the database host is usually its service name, not `127.0.0.1`.

## 4. Application structure

The walkthrough creates a small application called `sample_app`. Place it at
the checkout root while following this guide, or inside your own application
directory after installing the library there.

Create these directories and files:

```text
sample_app/
├── __init__.py
├── database.py
├── main.py
└── items/
    ├── __init__.py
    ├── models.py
    ├── schemas.py
    └── routes.py
```

Both `__init__.py` files can be empty. They make the directories regular Python
packages. Database infrastructure stays separate from the item context's
models, validation and HTTP route composition.

Run later commands from the directory containing `sample_app`, not from inside
that package.

## 5. Database and session configuration

Create `sample_app/database.py`:

```python
"""Configure PostgreSQL persistence and per-request sessions."""

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata for this application's mapped models."""


database_url = os.environ["DATABASE_URL"]
if not database_url.startswith("postgresql+asyncpg://"):
    raise ValueError("DATABASE_URL must use postgresql+asyncpg://.")

engine = create_async_engine(database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=True)


async def database_session() -> AsyncIterator[AsyncSession]:
    """Provide one caller-owned session for each request."""
    async with session_factory() as session:
        yield session
```

What each part does:

- `Base` owns the application's model metadata.
- `create_async_engine` creates an async PostgreSQL connection pool.
- `pool_pre_ping` checks pooled connections before reusing them.
- `async_sessionmaker` is a session factory, not a shared session.
- `database_session` yields a session and closes it after the request.
- `expire_on_commit=True` is supported because created and updated records are
  explicitly reloaded. You can also use `False`.

Pass the dependency function itself as `db_session=database_session`. Do not
call it, pass the factory, or create one global `AsyncSession` for all requests.

## 6. SQLAlchemy models

Create `sample_app/items/models.py`:

```python
"""Map item records to PostgreSQL."""

from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from sample_app.database import Base


class Item(Base):
    """An item with a generated identifier and a unique name."""

    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
```

The model defines storage rules: primary key, lengths, nullability and
uniqueness. In this example:

- PostgreSQL stores UUID identifiers.
- SQLAlchemy generates a UUID when inserting a record.
- `name` is required and unique.
- `description` is nullable.

Models need exactly one primary key. UUID, integer and string keys are supported;
composite keys are not.

## 7. Pydantic schemas

Create `sample_app/items/schemas.py`:

```python
"""Define the item HTTP request and response contracts."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Writable fields accepted by POST."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Notebook",
                    "description": "A paper notebook",
                }
            ]
        },
    )

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class ItemRead(ItemCreate):
    """Fields returned after loading an ORM record."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
```

Schemas and models have different responsibilities:

| Definition | Responsibility |
| --- | --- |
| SQLAlchemy `Item` | Store records and enforce database constraints |
| Pydantic `ItemCreate` | Validate writable fields in incoming JSON |
| Pydantic `ItemRead` | Describe the public fields clients receive |
| Generated PATCH schema | Allow omission while validating supplied values |

Important details:

- Keep database-generated identifiers out of required POST fields.
- `extra="forbid"` rejects unexpected input fields. The library does not enable
  this setting on your behalf.
- `from_attributes=True` lets output schemas read SQLAlchemy attributes.
- `str | None` permits null. Adding `default=None` also permits omission. In
  Pydantic v2, a nullable annotation without a default is still required.
- Match schema length constraints to database columns to reject invalid values
  before a write.
- Schema validation does not replace PostgreSQL uniqueness or foreign-key rules.
- Examples are optional: they improve OpenAPI documentation but are not required
  to create the router.

Only expose public response fields. A model can contain internal data that does
not belong in an HTTP response.

### Optional custom PATCH schema

An ordinary partial update does not require another schema. To allow changes
only to the description, append this class to the same schema file:

```python
class ItemDescriptionPatch(BaseModel):
    """Allow only description updates, including explicit null."""

    model_config = ConfigDict(extra="forbid")
    description: str | None = Field(default=None, max_length=500)
```

Import it in `routes.py` and pass
`request_patch_schema=ItemDescriptionPatch` to `Router`.

An explicit PATCH schema is used as supplied: required fields remain required.
Automatic partial-schema generation applies only when `request_patch_schema`
is omitted.

## 8. CRUD router configuration

Create `sample_app/items/routes.py`:

```python
"""Compose HTTP operations for the item context."""

from api_crud_generate_libary import Router
from sample_app.database import database_session
from sample_app.items.models import Item
from sample_app.items.schemas import ItemCreate, ItemRead

item_router = Router(
    model_class=Item,
    standard_schema=ItemCreate,
    db_session=database_session,
    response_get_schema=ItemRead,
    response_get_by_id_schema=ItemRead,
    response_post_schema=ItemRead,
    response_patch_schema=ItemRead,
)

router = item_router.router
```

`Router` is the CRUD builder; its `.router` attribute is the FastAPI `APIRouter`
to include in your application.

Here, `standard_schema=ItemCreate` supplies POST fields and the base for automatic
PATCH generation. All four record responses use `ItemRead` so the generated
identifier is returned.

When creation needs a different contract, set `request_post_schema`. Automatic
PATCH generation still uses `standard_schema`, not `request_post_schema`.

For compatibility, the original import remains valid:

```python
from api_crud_generate_libary.routers.router import Router
```

## 9. FastAPI startup

Create `sample_app/main.py`:

```python
"""Initialize infrastructure and connect the feature routers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sample_app.database import Base, engine
from sample_app.items.routes import router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialize demo tables and release the pool on shutdown."""
    del application
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Item CRUD API", lifespan=lifespan)
app.include_router(router, prefix="/items", tags=["Items"])
```

Importing the item routes registers the model before `create_all` runs.

This demo creates missing tables at startup. It does not create the database,
alter existing columns or apply migrations. See section 17 before changing
models backed by existing tables.

With the environment active and `DATABASE_URL` configured, start the server:

```bash
python -m uvicorn sample_app.main:app --reload
```

The colon separates the module from its `app` object. Use `--reload` for local
development.

Open:

- [Swagger UI](http://127.0.0.1:8000/docs) for interactive endpoint documentation.
- [ReDoc](http://127.0.0.1:8000/redoc) for reference documentation.
- [OpenAPI JSON](http://127.0.0.1:8000/openapi.json) for machine-readable contracts.

## 10. Calling every endpoint

The following `curl` examples use Bash quoting. On Windows, use Swagger UI,
`Invoke-RestMethod`, or `curl.exe` with quoting appropriate for your shell.

### Create one item

```bash
curl -X POST http://127.0.0.1:8000/items -H 'Content-Type: application/json' -d '{"name":"Notebook","description":"A paper notebook"}'
```

Example response:

```json
{
  "data": {
    "name": "Notebook",
    "description": "A paper notebook",
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

The identifier is illustrative; copy the actual value from your response.
POST returns HTTP 200 for compatibility.

POST accepts **exactly one JSON object**. Arrays, including an empty array,
return HTTP 422. Batch creation is not supported.

PowerShell equivalent:

```powershell
$body = @{
    name = "Notebook"
    description = "A paper notebook"
} | ConvertTo-Json
$created = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/items" -ContentType "application/json" -Body $body
$itemId = $created.data.id
```

### List items

```bash
curl http://127.0.0.1:8000/items
```

An empty unpaginated listing returns:

```json
{"data": []}
```

The array contains your records when any exist. Pagination metadata is omitted
when pagination is not requested.

### Paginate and sort

```bash
curl 'http://127.0.0.1:8000/items?page=1&items_per_page=20&order_by=name&direction=asc'
```

Example response:

```json
{
  "data": [
    {
      "name": "Notebook",
      "description": "A paper notebook",
      "id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

Pagination rules:

- Provide both `page` and `items_per_page`, or neither.
- `page` starts at 1; `items_per_page` must be greater than 0.
- A missing member of the pair returns 400; out-of-range query values return 422.
- A page beyond the last page returns an empty array and the total count.
- `total_count` counts root records, not the current page size.
- `has_more` indicates whether another page has records.
- Without pagination there is no extra count query or built-in result limit.

Sorting rules:

- Supply one direction for each field.
- Use `asc` or `desc`, case-insensitively.
- Only mapped scalar columns are valid sort fields.
- Invalid fields, mismatched lists and invalid directions return 400.
- Pagination adds primary-key ordering to break ties.

Repeat query keys to sort by more than one column:

```text
/items?page=1&items_per_page=20&order_by=name&direction=asc&order_by=id&direction=desc
```

### Read one item

Replace `ITEM_ID` with the identifier from POST:

```bash
curl http://127.0.0.1:8000/items/ITEM_ID
```

The response uses `{"data": {...}}`. An unknown identifier returns 404; a
malformed UUID or integer identifier returns 400.

### Update selected fields

```bash
curl -X PATCH http://127.0.0.1:8000/items/ITEM_ID -H 'Content-Type: application/json' -d '{"description":"Updated description"}'
```

`name` remains unchanged. The response uses the complete configured output
schema, not just the fields sent in PATCH.

### Delete an item

```bash
curl -X DELETE http://127.0.0.1:8000/items/ITEM_ID
```

The default response is HTTP 200 and a JSON string:

```json
"Item deleted"
```

To return an object, import `MessageSchema` in `routes.py`:

```python
from api_crud_generate_libary import MessageSchema
```

Add `response_delete_schema=MessageSchema` to the existing constructor. The
response becomes:

```json
{"message": "Item deleted"}
```

A custom DELETE schema must validate an object containing
`message="Item deleted"`. Other required fields need defaults or must be derived
by that schema. DELETE does not return the deleted database record.

## 11. Partial update behavior

By default, PATCH uses a partial version of `standard_schema`. Constraints,
aliases and validators are inherited while field omission becomes valid.

| PATCH input | Behavior with the guide's schemas |
| --- | --- |
| `{"name": "New name"}` | Update name and keep description |
| `{"description": null}` | Clear the nullable description |
| `{"name": null}` | Reject with 422: name is not nullable |
| `{"name": ""}` | Reject with 422: name needs at least one character |
| `{}` | Return the unchanged item |
| `{"unknown": "value"}` | Reject with 422: extra fields are forbidden |

Omitted fields are excluded from updates; their schema defaults are not written
to the database. Explicit null and omission therefore have different meanings.
POST applies input-schema defaults; PATCH writes only explicitly supplied fields.

Avoid full-object validators that assume every field is present on an automatic
partial schema. Use a dedicated PATCH schema when update rules differ from
creation rules.

PATCH preserves the primary key. Keep identifiers out of input schemas when
they are not writable; this guide rejects an incoming `id` as an extra field.
Nested relationships cannot be assigned through PATCH; update their scalar
foreign-key columns instead.

## 12. Complete configuration reference

| Parameter | Default | Purpose |
| --- | --- | --- |
| `model_class` | Required | SQLAlchemy mapped model |
| `standard_schema` | Required | Fallback schema and source of automatic PATCH fields |
| `db_session` | Required | FastAPI dependency yielding an `AsyncSession` |
| `request_post_schema` | `standard_schema` | Single-object POST input |
| `request_patch_schema` | Partial `standard_schema` | Explicit PATCH input |
| `response_get_schema` | `standard_schema` | Each record in a listing |
| `response_get_by_id_schema` | `standard_schema` | Lookup response record |
| `response_post_schema` | `standard_schema` | Created record |
| `response_patch_schema` | `standard_schema` | Updated record |
| `response_delete_schema` | JSON string | Optional DELETE message model |
| `use_get` | `True` | Enable listing |
| `use_get_by_id` | `True` | Enable lookup |
| `use_post` | `True` | Enable single-object creation |
| `use_patch` | `True` | Enable partial updates |
| `use_delete` | `True` | Enable deletion |
| `auth_callback` | `None` | One dependency callable or a sequence |
| `join_parameters` | `None` | Direct relationship loads |
| `second_level_join_parameters` | `None` | Nested relationship paths |

Set `use_post=False`, `use_patch=False` and `use_delete=False` for a read-only
router. Disabled operations are absent from the router and its OpenAPI document.

Configure URL prefixes and tags with FastAPI's `app.include_router(...)`; the
builder has no `prefix` or `tags` constructor parameters.

## 13. Authentication

Supply authentication through FastAPI dependencies. For a small API-key
example, create `sample_app/authentication.py`:

```python
"""Validate an application-supplied API key."""

import os
from secrets import compare_digest
from typing import Annotated

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

expected_api_key = os.environ["API_KEY"]
if not expected_api_key:
    raise ValueError("API_KEY cannot be empty.")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    """Reject requests without the configured application key."""
    if api_key is None or not compare_digest(
        api_key.encode("utf-8"), expected_api_key.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid API key.")
```

Set a non-empty `API_KEY` environment variable before restarting the application.
Import `require_api_key` in `sample_app/items/routes.py` and add
`auth_callback=[require_api_key]` to the constructor.

Clients send the `X-API-Key` header. Every enabled operation uses the configured
dependencies. A single callable is also accepted; a sequence can contain
multiple callables.

This demonstrates API-key integration, not a built-in user or JWT system. Supply
your existing dependencies for JWT or permissions. The library does not issue
tokens, enforce record ownership, filter tenants or use dependency return values
as query filters.

## 14. Relationships

Define actual SQLAlchemy relationships and matching output schemas before
enabling eager loading.

For example, an item can belong to a category. Replace the contents of
`sample_app/items/models.py` with this complete relationship-aware version:

```python
"""Map items and categories with bidirectional relationships."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sample_app.database import Base


class Category(Base):
    """A category referenced by item records."""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80))
    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(Base):
    """An item that can optionally reference an existing category."""

    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"))
    category: Mapped[Category | None] = relationship(back_populates="items")
```

Append the following contracts to `sample_app/items/schemas.py`, retaining the
existing imports, `ItemCreate` and `ItemRead` definitions:

```python
class ItemCreateWithCategory(ItemCreate):
    """Accept a category identifier when creating or updating an item."""

    category_id: UUID | None = None


class CategoryRead(BaseModel):
    """Serialize a loaded category."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class ItemWithCategory(ItemRead):
    """Serialize an item and its eagerly loaded category."""

    category_id: UUID | None
    category: CategoryRead | None


class CategoryWithItems(CategoryRead):
    """Serialize a category with a finite collection of item records."""

    items: list[ItemRead]


class CategoryWithNestedItems(CategoryRead):
    """Serialize a category, its items, and each item's category."""

    items: list[ItemWithCategory]
```

In the existing constructor:

- Import `ItemCreateWithCategory` and `ItemWithCategory` in `routes.py`.
- Use `standard_schema=ItemCreateWithCategory`.
- Set all four record response schemas to `ItemWithCategory`.
- Add `join_parameters=[{"response_parameter": Item.category}]`.

Create categories through PostgreSQL or another CRUD router before referencing
their identifiers. Creating an item does not create nested category records.

For a category router, use `CategoryWithItems` as the listing/lookup output
schema and `join_parameters=[{"response_parameter": Category.items}]`.
Define a separate category input schema with only `name`; the UUID is generated
by the model, as it is for items.

For a nested category -> items -> category path, use:

```python
nested_relationships = [
    {"response_parameter": [Category.items, Item.category]},
]
```

Pass it as `second_level_join_parameters` on the category router and use
`CategoryWithNestedItems` as its listing/lookup output schema. This includes a
category object inside each item without recursively including its items again.

Relationship rules:

- Pass mapped attributes such as `Item.category`, not strings.
- `response_parameter` is one attribute for a direct load, or a non-empty list
  of consecutive attributes for a nested load.
- Each ORM-backed response level needs `from_attributes=True`.
- Configure every relationship accessed during serialization for eager loading.
- Scalar and collection relationships are supported.
- Collection loading deduplicates root records and preserves page boundaries.
- Legacy `model`, `column`, `first_model` and `second_model` keys are accepted;
  relationship mappings now determine eager loading.

Changing the model requires a migration or a fresh demo database. Restarting
alone does not add `category_id` to an existing table.

## 15. Primary key alternatives

The router discovers the primary key instead of requiring a field named `id`.
For example, replace the UUID declaration with one of these alternatives:

```python
# Integer primary key:
# item_number: Mapped[int] = mapped_column(primary_key=True)

# String primary key:
# sku: Mapped[str] = mapped_column(String(40), primary_key=True)
```

These are alternatives, not additional primary keys. Keep a database-generated
integer key out of the input schema and include it in the output schema. A
string key without a database default must be supplied by the creation schema.

The path remains `/{id_}`. Its parameter name does not require a model field
with the same name. Integer and UUID identifiers are converted to their mapped
Python type. Unsupported or composite keys are rejected during configuration.

## 16. Sessions, transactions and failures

The application owns session lifetime. The library never closes an injected
session and supports both values of `expire_on_commit`.

Each successful POST, PATCH or DELETE commits that session. Do not keep
unrelated pending writes in it: those writes would share the commit. Do not
share one session across concurrent requests.

Created and updated records and their configured relationships are reloaded
after commit. Database errors handled by the persistence layer trigger rollback
so the session can be reused.

| Failure | HTTP status |
| --- | --- |
| Malformed identifier or invalid/incomplete sorting | 400 |
| Incomplete pagination pair | 400 |
| Invalid body or out-of-range query value | 422 |
| Record not found | 404 |
| Unique, foreign-key, not-null or other integrity constraint | 409 |
| Invalid PostgreSQL value, including excessive string length | 400 |
| Recognized database availability failure | 503 |
| Other handled database operation failure | 500 |

Handled database failure messages do not expose SQL, driver details or stored
values. Authentication dependencies determine their own failure responses.

Input validation fails before persistence. An incorrectly configured output
schema can fail after a mutation has committed; align its fields with the model
and eager-loading configuration.

This version does not provide batch writes, externally managed multi-operation
transactions, arbitrary query filtering, composite keys or other database
drivers.

## 17. Database migrations

`Base.metadata.create_all` is suitable for an initial local demonstration.
Use a migration tool such as Alembic for applications with existing data.

From the application root:

```bash
python -m pip install alembic
python -m alembic init -t async migrations
```

In the generated `migrations/env.py`, import the application metadata and models,
configure the URL, and replace `target_metadata = None`:

```python
import os

from sample_app.database import Base
from sample_app.items.models import Item

# Importing Item registers its table in Base.metadata.
target_metadata = Base.metadata

# Escape percent signs for Alembic's ConfigParser interpolation.
config.set_main_option(
    "sqlalchemy.url",
    os.environ["DATABASE_URL"].replace("%", "%%"),
)
```

This modifies Alembic's generated file; retain its async migration functions and
existing `config` initialization. Set the URL after `config = context.config`.

Generate a revision, inspect its operations, then apply it:

```bash
python -m alembic revision --autogenerate -m "Create item table"
python -m alembic upgrade head
```

Remove the `create_all` startup block from a migration-managed application;
keep pool disposal in the lifespan.

Start with a fresh database for this migration path. If tables already exist
from `create_all`, establish an appropriate Alembic baseline first; do not assume
autogeneration will reproduce their creation as an initial revision.

## 18. Existing runnable example

For a ready-made application, use [examples/postgresql](examples/postgresql)
instead of creating `sample_app`.

With the library and Uvicorn installed and `DATABASE_URL` set, run from the
checkout root:

```bash
python -m uvicorn examples.postgresql.app:app --reload
```

That example creates `example_items` and exposes the same `/items` operations.
It separates database configuration, models, schemas and composition. Do not
run both demo applications on the same HTTP port at once.

## 19. Contributor setup, tests and packaging

This section is for library contributors, rather than applications importing it.

Use the repository's `develop` branch. If your checkout only has `main` and no
remote `develop`, create `develop` from `main` before editing. Read
[AGENTS.md](AGENTS.md) for development and commit rules.

With Poetry installed:

```bash
poetry install --with dev
poetry check --strict
poetry run black --check api_crud_generate_libary tests examples
poetry run pylint api_crud_generate_libary tests examples
poetry run pytest -q
```

PostgreSQL tests require a dedicated test database and a role with permission
to create schemas. Create an empty `crud_tests` database owned by `crud_user`,
then configure:

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://crud_user:local_dev_password@127.0.0.1:5432/crud_tests"
poetry run pytest -q
```

Or on Linux/macOS:

```bash
export TEST_DATABASE_URL='postgresql+asyncpg://crud_user:local_dev_password@127.0.0.1:5432/crud_tests'
poetry run pytest -q
```

Tests create and drop only their randomly named schemas. They do not use
existing application tables. Without `TEST_DATABASE_URL`, PostgreSQL tests are
explicitly skipped; the remaining tests still run.

CI is configured to run formatting, static analysis, tests and packaging with
PostgreSQL 16 on Python 3.13 and 3.14.

Build and validate distributions:

```bash
poetry build
poetry run twine check dist/*
```

Wheel and source distributions include the MIT license. Before a public
release, verify package-name availability and test installation in a fresh
environment and through TestPyPI. Building does not publish anything.

Maintainers: follow the [publishing guide](https://github.com/pedro-vlps/api_crud_generate_libary/blob/main/docs/PUBLISHING.md)
to configure trusted publishers, approve a release tag, test TestPyPI and
manually publish to PyPI using the `Publish package` GitHub Actions workflow.

Commits require approval under `AGENTS.md`; pushing and publication require
separate authorization.

## 20. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Library import fails | Activate the intended environment and install with its `python -m pip` |
| `sample_app` import fails | Run Uvicorn from the directory containing the package |
| Missing `DATABASE_URL` | Set it in the same terminal before startup |
| Missing `greenlet` | Install this version's declared dependencies, including `sqlalchemy[asyncio]` |
| Connection refused | Confirm PostgreSQL is running and check host and port |
| Database authentication fails | Check the PostgreSQL role, password and database |
| A table is absent | Initialize demo tables or run migrations against the intended database |
| A new column is absent | Apply a migration; `create_all` does not alter existing tables |
| POST rejects a list | Send one JSON object instead of an array |
| POST requires an ID | Remove generated identifiers from required input fields |
| PATCH requires every field | Omit `request_patch_schema` or correct that schema's required fields |
| Unexpected fields return 422 | Check the schema's `extra="forbid"` contract |
| Duplicate name returns 409 | Supply a unique value or intentionally change the database rule |
| Relationship serialization raises `MissingGreenlet` | Configure eager loading and ORM-compatible output schemas |
| DELETE returns a string | Set `response_delete_schema=MessageSchema` for an object response |
| Integration tests are skipped | Configure a PostgreSQL `TEST_DATABASE_URL` |

## 21. License

This project uses the [MIT License](LICENSE).

You may use, modify and distribute the software, including commercially,
subject to the license terms. Preserve the copyright and permission notice in
copies or substantial portions. The software is provided without warranty.
