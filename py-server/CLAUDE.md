# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Early scaffold for a Python web server. `main.py` is still the `uv init` hello-world. There is no application code, test suite or package layout yet. Declared dependencies point to the intended stack: FastAPI for the HTTP layer, SQLAlchemy for persistence against PostgreSQL, Ruff for lint/format, Pyrefly for type checking.

The git repository root is the parent directory (`AI-Webserver/`). This project lives in the `py-server/` subfolder.

## Tooling

The project is managed with **uv** and targets **Python 3.15** (`.python-version`, `requires-python = ">=3.15"`). The virtualenv lives in `.venv`.

```sh
uv sync                      # install dependencies from uv.lock
uv run main.py               # run the entry point
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

Neither a PostgreSQL driver (e.g. `psycopg`) nor an ASGI server (e.g. `uvicorn`) is in the dependencies yet. Add them before wiring SQLAlchemy to Postgres or serving the FastAPI app.
