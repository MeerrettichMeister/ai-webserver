# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

A FastAPI recipe API, packaged as `src/py_server` (src layout, built with `uv_build`), in layers:
routers → services → repositories → models. Each layer only calls the one below it.

- `main.py`: the FastAPI `app`, its startup (`lifespan`: seeds recipes, so the app needs a
  migrated database to start) and the handler mapping `ServiceError`s to HTTP status codes (it
  does not create tables; see Migrations)
- `seed/`: recipes that always exist. Each is a `POST /recipes` body (`seed/Pfannkuchen.json`)
  with a fixed id in `SEED_RECIPES`; on startup the missing ones are created, existing (also
  edited) ones are left alone, deleted ones come back. The JSON ships inside the package, so it
  is also in the Docker image
- `config.py`: `Settings` read from env (`DATABASE_URL`), via `get_settings()`
- `db.py`: engine, the per-request `get_session` dependency and `SessionDep`
- `model/`: SQLAlchemy ORM, one module per table (`base.py` holds `Base`): a `Recipe` owns its
  `Ingredient`s (numeric amount, unit) and ordered `Step`s (plain text). Relationship
  types from other modules are imported under `TYPE_CHECKING`. Import models from
  `py_server.model`: its `__init__.py` imports every model, so all tables are registered
- `dto/`: Pydantic request/response bodies, one module per resource, re-exported from
  `py_server.dto`. Each endpoint has its own body: `*Create` (`POST /recipes`), `*Replace`
  (nested in `PUT /recipes/{id}`), `*Update` (`PUT`/`PATCH` of that resource) and `*Read`
  (responses, based on `ReadModel`); `common.py` holds shared types. The API calls an
  ingredient's name `ingredient` (`Ingredient.name` in the ORM)
- Pagination (`dto/pagination.py`): `GET /recipes` takes `?page=&size=` (size ≤ 100) and returns
  a `Page[RecipeRead]` (`items`, `total`, `page`, `size`, `pages`). The repository pages in SQL
  (`LIMIT`/`OFFSET` plus a `count(*)`), ordered by `name, id` (the id makes the order total,
  so pages never overlap) and backed by the index `ix_recipe_name_id`. A route's query
  parameters go into one model (`Annotated[RecipeListQuery, Query()]`): FastAPI only expands a
  query model into separate parameters if it is the route's only query parameter
- `seed/Pfannkuchen.json` is also the reference body for `POST /recipes`; it must keep working
  unchanged (startup fails if it no longer validates against `RecipeCreate`)
- `repository/`: data access, one repository per table on the request's session. Only queries
  and stages changes (`add`, `delete`); never commits
- `service/`: business logic, one service per resource. Each public method is one transaction:
  it takes and returns DTOs (`Model.model_validate(orm_obj)`), commits via
  `service.versioning.commit()`, and signals failures with the `ServiceError` subclasses in
  `service/errors.py` (not `HTTPException`)
- `routers/`: HTTP only, one `APIRouter` per resource: path/query/header parameters, ETag
  headers, status codes. Routes get their service through a `*ServiceDep` dependency, declare the
  DTO they return as the return type, and use neither SQLAlchemy nor the ORM models
- `etags.py`: optimistic locking over HTTP. `Recipe`, `Ingredient` and `Step` have a `version`
  exposed as `ETag`; writes require `If-Match` (428 if missing), which `IfMatchDep` parses into
  an `ExpectedVersion` that the service checks (412 if stale). `Recipe.version` covers the whole
  aggregate: every write to a recipe or its children must call `recipe.touch()`

There is no test suite yet.

The git repository root is the parent directory (`AI-Webserver/`). This project lives in the `py-server/` subfolder.

## Tooling

The project is managed with **uv** and targets **Python 3.15** (`.python-version`, `requires-python = ">=3.15"`). The virtualenv lives in `.venv`.

```sh
uv sync                      # install dependencies from uv.lock
uv run uvicorn py_server.main:app --reload   # run the API (docs at /docs)
uv add <pkg>                 # add a dependency (updates pyproject.toml + uv.lock)

uv run ruff check .          # lint
uv run ruff check --fix .    # lint with autofix
uv run ruff format .         # format
uv run pyrefly check         # type check
```

Ruff and Pyrefly are in the `dev` dependency group (`uv add --dev <pkg>` for more dev tools). Their configuration lives in `pyproject.toml` (`[tool.ruff]`, `[tool.pyrefly]`). Ruff uses a 100-char line length and bans `print` (T20); use logging instead.

## Database

`scripts/docker-compose.yaml` defines a local PostgreSQL 18 container (db/user/password all `postgres`, port `5432`):

```sh
docker compose -f scripts/docker-compose.yaml up -d
```

SQLAlchemy talks to Postgres via psycopg 3 (`psycopg[binary]`, bundles libpq), so connection URLs use the `postgresql+psycopg://` scheme, e.g. `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres`. Set `DATABASE_URL` to use a different database. Use `127.0.0.1`, not `localhost`: on Windows `localhost` resolves to `::1` first, where the Docker port forward accepts the connection but never answers, so connecting hangs forever.

## Migrations

Alembic manages the schema. Config is in `pyproject.toml` (`[tool.alembic]`, there is no `alembic.ini`); scripts are in `migrations/`, and `migrations/env.py` reads `DATABASE_URL` and `Base.metadata`.

```sh
uv run alembic upgrade head                          # apply migrations (run before starting the app)
uv run alembic revision --autogenerate -m "<what>"   # after changing model/; review the result
uv run alembic check                                 # fail if model/ has changes without a migration
uv run alembic downgrade -1                          # undo the last migration
```

Nothing has been deployed yet, so everything is in one revision, `initial schema`. Once there is a deployed database, add new revisions instead of editing that one.

Generated revisions are run through `ruff check --fix` and `ruff format` automatically. Constraint names come from the naming convention on `Base.metadata`, so migrations can refer to them. Autogenerate does not detect everything (e.g. renamed columns or tables show up as drop + add), so always read the generated script.

Plain `uvicorn` is used deliberately, not `uvicorn[standard]` / `fastapi[standard]`: those extras pull in C extensions (pyyaml, httptools, …) without Python 3.15 wheels, which fail to build on Windows without MSVC.

## Container image and deployment

`Dockerfile` builds a two-stage image (`python:3.15-slim-trixie`, uv pinned to the local version): the build stage runs `uv sync --locked --no-dev --no-editable`, the runtime stage only gets the venv, `pyproject.toml` and `migrations/` and runs uvicorn on port 8000 as a non-root user. `.dockerignore` is an allowlist; add new top-level files the build needs there.

`compose.yaml` is for deployment (unlike `scripts/docker-compose.yaml`, the local dev database): `db` (postgres:18, volume on `/var/lib/postgresql`, no published port), `migrate` (runs `alembic upgrade head`, then exits) and `api` (starts once `migrate` succeeded). Settings come from `.env` (template: `.env.example`; `POSTGRES_PASSWORD` is required).

```sh
cp .env.example .env            # set POSTGRES_PASSWORD
docker compose up -d --build    # this machine has Podman: `podman compose ...` works the same
docker compose down             # add -v to also delete the database volume
```
