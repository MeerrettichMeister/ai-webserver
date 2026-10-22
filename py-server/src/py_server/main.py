from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from py_server.routers import ingredients, recipes, steps
from py_server.service import (
    ConflictError,
    InvalidReferenceError,
    NotFoundError,
    PreconditionFailedError,
    ServiceError,
)

# The schema is managed by Alembic: run `uv run alembic upgrade head` before starting.
app = FastAPI(title="Recipe API")
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
