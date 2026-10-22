# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

A FastAPI recipe API, packaged as `src/py_server` (src layout, built with `uv_build`):

- `main.py`: the FastAPI `app` (it does not create tables; see Migrations)
- `config.py`: `Settings` read from env (`DATABASE_URL`), via `get_settings()`
- `db.py`: engine, the per-request `get_session` dependency and `SessionDep`
- `model/`: SQLAlchemy ORM, one module per table (`base.py` holds `Base`): a `Recipe` owns its
  `Ingredient`s (amount, unit) and ordered `Step`s (each uses one ingredient). Relationship
  types from other modules are imported under `TYPE_CHECKING`. Import models from
  `py_server.model`: its `__init__.py` imports every model, so all tables are registered
- `dto/`: Pydantic request/response bodies, one module per resource, re-exported from
  `py_server.dto`. Each endpoint has its own body: `*Create` (nested in `POST /recipes`),
  `*Replace` (nested in `PUT /recipes/{id}`), `*Update` (`PUT`/`PATCH` of that resource) and
  `*Read` (responses, based on `ReadModel`); `common.py` holds shared types
- `etags.py`: optimistic locking over HTTP. `Recipe`, `Ingredient` and `Step` have a `version`
  exposed as `ETag`; `PUT` requires a matching `If-Match` (428 if missing, 412 if stale).
  `Recipe.version` covers the whole aggregate: every write to a recipe or its children must call
  `recipe.touch()` and commit via `commit_or_412()`
- `routers/`: one `APIRouter` per resource; `get_*_or_404` dependencies load path objects

Routes return Pydantic models (`Model.model_validate(orm_obj)`) and declare them as the return type.
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

Generated revisions are run through `ruff check --fix` and `ruff format` automatically. Constraint names come from the naming convention on `Base.metadata`, so migrations can refer to them. Autogenerate does not detect everything (e.g. renamed columns or tables show up as drop + add), so always read the generated script.

Plain `uvicorn` is used deliberately, not `uvicorn[standard]` / `fastapi[standard]`: those extras pull in C extensions (pyyaml, httptools, …) without Python 3.15 wheels, which fail to build on Windows without MSVC.
