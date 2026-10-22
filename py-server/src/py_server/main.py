from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from py_server.db import get_engine
from py_server.models import Base
from py_server.routers import ingredients, recipes, steps


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # No migrations yet: create any missing tables on startup.
    Base.metadata.create_all(get_engine())
    yield


app = FastAPI(title="Recipe API", lifespan=lifespan)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(steps.router)
