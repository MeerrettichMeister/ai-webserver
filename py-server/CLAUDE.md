# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

A FastAPI recipe API, packaged as `src/py_server` (src layout, built with `uv_build`):

- `main.py`: the FastAPI `app`; its lifespan runs `create_all` (there are no migrations yet)
- `config.py`: `Settings` read from env (`DATABASE_URL`), via `get_settings()`
- `db.py`: engine, the per-request `get_session` dependency and `SessionDep`
- `models.py`: SQLAlchemy ORM: a `Recipe` owns its `Ingredient`s (amount, unit) and ordered `Step`s (each uses one ingredient)
- `schemas.py`: Pydantic request/response models (`*Create`, `*Read`)
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

SQLAlchemy talks to Postgres via psycopg 3 (`psycopg[binary]`, bundles libpq), so connection URLs use the `postgresql+psycopg://` scheme, e.g. `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`. Set `DATABASE_URL` to use a different database.

Plain `uvicorn` is used deliberately, not `uvicorn[standard]` / `fastapi[standard]`: those extras pull in C extensions (pyyaml, httptools, …) without Python 3.15 wheels, which fail to build on Windows without MSVC.
