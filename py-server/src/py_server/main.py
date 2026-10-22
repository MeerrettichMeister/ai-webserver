"""The FastAPI application: routers, startup seeding and error responses."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from py_server.db import get_engine
from py_server.routers import ingredients, recipes, steps
from py_server.seed import seed_recipes
from py_server.service import (
    ConflictError,
    InvalidReferenceError,
    NotFoundError,
    PreconditionFailedError,
    ServiceError,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Before serving requests, create the seed recipes that are missing."""
    with Session(get_engine()) as session:
        seed_recipes(session)
    yield


# The schema is managed by Alembic: run `uv run alembic upgrade head` before starting.
app = FastAPI(title="Recipe API", lifespan=lifespan)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(steps.router)

_STATUS_CODES: dict[type[ServiceError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    PreconditionFailedError: status.HTTP_412_PRECONDITION_FAILED,
    InvalidReferenceError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


@app.exception_handler(ServiceError)
async def handle_service_error(_request: Request, exc: ServiceError) -> JSONResponse:
    """Answer like an HTTPException would: {"detail": message} with the error's status."""
    return JSONResponse({"detail": str(exc)}, status_code=_STATUS_CODES[type(exc)])
