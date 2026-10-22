"""Routes for the ingredients of a recipe."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from py_server.db import SessionDep
from py_server.dto import IngredientRead, IngredientUpdate
from py_server.etags import (
    NOT_MODIFIED_RESPONSES,
    PRECONDITION_RESPONSES,
    IfMatchDep,
    IfNoneMatchDep,
    etag,
    send_etag,
)
from py_server.service import IngredientService

router = APIRouter(prefix="/recipes/{recipe_id}/ingredients", tags=["ingredients"])


def get_ingredient_service(session: SessionDep) -> IngredientService:
    """Dependency: the ingredient service on the request's session."""
    return IngredientService(session)


IngredientServiceDep = Annotated[IngredientService, Depends(get_ingredient_service)]


@router.get("")
def list_ingredients(
    recipe_id: UUID,
    service: IngredientServiceDep,
    search: Annotated[
        str, Query(description="Only ingredients whose name contains this, ignoring case.")
    ] = "",
) -> list[IngredientRead]:
    """The recipe's ingredients by name, optionally filtered by name."""
    return service.find_all(recipe_id, search)


@router.get("/{ingredient_id}", responses=NOT_MODIFIED_RESPONSES)
def get_ingredient(
    recipe_id: UUID,
    ingredient_id: UUID,
    service: IngredientServiceDep,
    if_none_match: IfNoneMatchDep,
    response: Response,
) -> IngredientRead:
    """One ingredient; 304 if If-None-Match names its current version."""
    ingredient = service.get(recipe_id, ingredient_id)
    send_etag(response, ingredient.version, if_none_match)
    return ingredient


@router.put(
    "/{ingredient_id}",
    responses={
        **PRECONDITION_RESPONSES,
        status.HTTP_409_CONFLICT: {"description": "Another ingredient has this name"},
    },
)
def update_ingredient(
    recipe_id: UUID,
    ingredient_id: UUID,
    payload: IngredientUpdate,
    if_match: IfMatchDep,
    service: IngredientServiceDep,
    response: Response,
) -> IngredientRead:
    """Change one ingredient; requires If-Match with its current version."""
    ingredient = service.update(recipe_id, ingredient_id, payload, if_match)
    response.headers["ETag"] = etag(ingredient.version)
    return ingredient
