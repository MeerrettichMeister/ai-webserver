# Recipe API

A REST API for recipes, each with its details (servings, total time in minutes, difficulty
`easy`/`medium`/`hard`), its ingredients and its ordered preparation steps. Built with FastAPI,
SQLAlchemy and PostgreSQL. The Pfannkuchen recipe
([`seed/Pfannkuchen.json`](src/py_server/seed/Pfannkuchen.json)) is always available: the app
creates it on startup if it is missing. More example recipes to `POST` are in
[`recipes/`](recipes).

In the database a recipe has exactly one `recipe_details` row (1:1; its primary key is the
recipe's id) and any number of `ingredient` and `step` rows (1:N).

## Run locally

Requires [uv](https://docs.astral.sh/uv/) and Docker (or Podman) for the database.

```sh
uv sync                                          # install dependencies
docker compose -f scripts/docker-compose.yaml up -d   # PostgreSQL on localhost:5432
uv run alembic upgrade head                      # create the tables
uv run uvicorn py_server.main:app --reload       # http://127.0.0.1:8000
```

Interactive API docs are at <http://127.0.0.1:8000/docs>. Set `DATABASE_URL` to use another
database (default: `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres`).

## Run with Docker

`compose.yaml` runs the API with its own database and applies migrations before the API starts:

```sh
cp .env.example .env            # set POSTGRES_PASSWORD
docker compose up -d --build    # API on http://localhost:8000
```

## API

| Method | Path | |
|---|---|---|
| `GET` | `/recipes` | Recipes by name, paginated (`?page=1&size=20`, `?search=`); without ingredients and steps |
| `POST` | `/recipes` | Create a recipe ([example body](src/py_server/seed/Pfannkuchen.json)) |
| `GET` | `/recipes/{id}` | A recipe with its ingredients and steps |
| `PUT` | `/recipes/{id}` | Replace the whole recipe |
| `PATCH` | `/recipes/{id}` | Rename a recipe |
| `DELETE` | `/recipes/{id}` | Delete a recipe |
| `GET` | `/recipes/{id}/ingredients` | A recipe's ingredients (`?search=`) |
| `GET`, `PUT` | `/recipes/{id}/ingredients/{ingredient_id}` | Read or change one ingredient |
| `GET` | `/recipes/{id}/steps` | A recipe's steps in order |
| `GET`, `PUT` | `/recipes/{id}/steps/{step_id}` | Read or change one step |

A list page looks like `{"items": [...], "total": 45, "page": 1, "size": 20, "pages": 3}`.

### Concurrent changes

Recipes, ingredients and steps have a `version`, also sent as the `ETag` header. `PUT` and
`PATCH` require an `If-Match` header with the version the change is based on (`"3"` or `3`):

- missing header: `428 Precondition Required`
- version is no longer current: `412 Precondition Failed`; fetch it again and retry

A recipe's version also changes when one of its ingredients or steps changes.

`GET` on a single recipe, ingredient or step is conditional: with `If-None-Match` naming the
current version (`"3"` or `3`), the answer is `304 Not Modified` without a body.

## Development

```sh
uv run ruff check .     # lint
uv run ruff format .    # format
uv run pyrefly check    # type check
uv run alembic revision --autogenerate -m "<what>"   # after changing the models
```

The code is layered: `routers/` (HTTP) → `service/` (business logic) → `repository/` (database
queries) → `model/` (SQLAlchemy tables); request and response bodies are in `dto/`.
