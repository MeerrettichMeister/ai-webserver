from fastapi import FastAPI

from py_server.routers import ingredients, recipes, steps

# The schema is managed by Alembic: run `uv run alembic upgrade head` before starting.
app = FastAPI(title="Recipe API")
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(steps.router)
