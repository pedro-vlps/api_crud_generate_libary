# Changelog

## v1.2.0 - 2026-10-16

- Adopt the MIT license and include it in package metadata and distributions.
- Document PyPI and source installation, database setup, schemas and CRUD integration.
- Fix PostgreSQL async dependencies and synchronize the development lockfile.
- Reload committed records and preserve caller-owned session lifetimes.
- Generate partial PATCH contracts and publish concrete OpenAPI request schemas.
- Accept only one object per POST request and reject arrays.
- Apply optional DELETE message schemas while preserving the default response.
- Support UUID, integer and string primary keys with mapped attribute names.
- Correct relationship loading, pagination, sorting validation and database errors.
- Add public package exports, an executable PostgreSQL example and regression tests.
- Add CI checks and adopt the project development instructions.
- Replace the obsolete automatic commit script with the documented approval workflow.

## v1.1.1

- Removed PatternGetSchema mentions and declaration (Deprecated)

## v1.1.0

- Added a option to send multiple dependencies to auth_callback parameter

## v1.0.5

- Removed status_code from delete route (It should not be here)

## v1.0.4

- Fixed some files imports after changing the main folder name
- Removed linter errors and type errors

## v1.0.3

- Changed the utf format of pyproject file from UTF-8 with BOM to UTF-8

## v1.0.2

- Changed pyproject name format

## v1.0.1

- Changed pyproject.toml name
- Changed main folder name

## v1.0.0

- Added all the files to generate a basic CRUD
- Added a basic documentation for the README.md file
- Created the development setup using poetry









