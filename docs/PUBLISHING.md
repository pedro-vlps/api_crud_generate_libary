# Publishing the library

The distribution name is `api-crud-generate-libary`; the Python import is
`api_crud_generate_libary`. Keep this existing spelling for compatibility.
The first prepared public version is `1.2.0`, supporting Python 3.13 or newer
and PostgreSQL with asyncpg. Building, committing and merging do not upload a
package. TestPyPI and PyPI are separate registries with separate accounts and
publisher settings.

## 1. Configure accounts and GitHub environments

1. Register accounts at [PyPI](https://pypi.org/account/register/) and
   [TestPyPI](https://test.pypi.org/account/register/).
2. Verify your email and configure two-factor authentication. Save recovery
   codes securely.
3. In `pedro-vlps/api_crud_generate_libary`, open **Settings > Environments**.
   Create environments named exactly `testpypi` and `pypi`.
4. Restrict these environments to the `main` branch. Configure required
   reviewers for `pypi` if available under your GitHub plan.

## 2. Register trusted publishers

Before the first upload, create a pending publisher on each registry:

- [TestPyPI publishing settings](https://test.pypi.org/manage/account/publishing/)
- [PyPI publishing settings](https://pypi.org/manage/account/publishing/)

Use the following values:

| Field | TestPyPI | PyPI |
| --- | --- | --- |
| PyPI project name | `api-crud-generate-libary` | `api-crud-generate-libary` |
| Owner | `pedro-vlps` | `pedro-vlps` |
| Repository name | `api_crud_generate_libary` | `api_crud_generate_libary` |
| Workflow filename | `publish.yml` | `publish.yml` |
| Environment name | `testpypi` | `pypi` |

If the registry project already exists under your account, add a publisher in
that project's publishing settings instead. A missing project page does not
guarantee that its name is available. Resolve any name conflict before release.

The workflow uses GitHub OIDC to request short-lived credentials. Do not add
PyPI API tokens to the repository, workflow or chat. A pending publisher can
create the project on its first successful upload.

## 3. Prepare and approve the release

Work on `develop`. Follow `AGENTS.md` for specific commit and tag approval.
For future releases, update `pyproject.toml`, applicable lock metadata and
`CHANGELOG.md` consistently before approval. Use a new version for each new
distribution: registry files cannot be overwritten.

Run all checks with a disposable PostgreSQL database configured through
`TEST_DATABASE_URL`:

```powershell
poetry install --with dev
poetry check --strict
poetry run black --check api_crud_generate_libary tests examples
poetry run pylint api_crud_generate_libary tests examples
poetry run pytest -q
poetry build --output dist/release-1.2.0
poetry run twine check dist/release-1.2.0/*
```

Use a new output directory for each release attempt to avoid uploading stale
artifacts. Inspect the README rendering, package metadata and included license.
The automated publishing workflow builds in a fresh checkout.

After specific commit approval and separate push authorization, merge the
approved setup into `main` and push both branches. Create the version tag only
after tag approval. For the initial release, from the approved `main` commit:

```powershell
git tag -a v1.2.0 -m "Release 1.2.0"
git push origin develop main
git push origin v1.2.0
```

Do not run these commands until the relevant approvals exist. Do not overwrite
an existing tag. The tag must include the reusable CI configuration from this
setup. Tagging or pushing alone does not publish anything.

## 4. Publish to TestPyPI

1. Open the repository's **Actions > Publish package > Run workflow**.
2. Select branch `main`, target `testpypi`, and release tag `v1.2.0`.
3. Run the workflow and inspect every job. It validates the tag, checks that
   its commit belongs to `main`, runs CI on Python 3.13 and 3.14 with PostgreSQL
   16, builds distributions and validates them with Twine.
4. The publishing job uploads the Python 3.13 build's wheel and source archive
   using the `testpypi` environment. It does not rebuild with upload credentials.
5. Verify the version and README at
   [the TestPyPI project](https://test.pypi.org/project/api-crud-generate-libary/).

A workflow dispatched from another branch is skipped. If publication fails,
inspect the failing job and publisher/environment spelling before retrying.
If files were already uploaded, inspect which files exist; do not assume that
retrying can replace them. Corrected package contents require a new version.

## 5. Test the uploaded distribution

Create an isolated environment outside the repository so source files cannot
hide installation errors. The following PowerShell commands use the Windows
Python launcher; on other systems use a Python 3.13+ executable:

```powershell
py -3.13 -m venv ../crud-pypi-smoke
$python = "../crud-pypi-smoke/Scripts/python.exe"
$python = (Resolve-Path $python).Path
& $python -m pip install --upgrade pip
& $python -m pip install "pydantic>=2.12.5,<3" "fastapi>=0.135.3,<0.136" "sqlalchemy[asyncio]>=2.0.49,<3" "asyncpg>=0.31.0,<0.32"
& $python -m pip install --index-url https://test.pypi.org/simple/ --no-deps "api-crud-generate-libary==1.2.0"
Push-Location ..
try {
    & $python -m pip check
    & $python -c "from importlib.metadata import version; from api_crud_generate_libary import Router; print(version('api-crud-generate-libary')); print(Router)"
} finally {
    Pop-Location
}
```

Install dependencies from PyPI first and the library from TestPyPI with
`--no-deps`; do not combine registries using `--extra-index-url`.
Run your application's CRUD smoke tests against a disposable PostgreSQL
database using this installed release before production publication.

## 6. Publish to PyPI

After the TestPyPI installation and application checks pass, manually run
**Publish package** again from `main`, now selecting `pypi` and the same
`v1.2.0` tag. Approve the GitHub environment deployment if configured.
The workflow rebuilds and retests the same source commit before uploading.

Verify the successful workflow and
[the PyPI version page](https://pypi.org/project/api-crud-generate-libary/1.2.0/).
Check installation in another clean environment:

```powershell
python -m pip install "api-crud-generate-libary==1.2.0"
python -m pip check
```

Application users can then install normally:

```powershell
python -m pip install api-crud-generate-libary
poetry add api-crud-generate-libary
```

No GitHub dependency is needed after publication. The existing README already
includes registry installation commands; its unpublished-version note can be
updated after verifying the actual first release.

## References

- [Trusted publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [Creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [Packaging Python projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
