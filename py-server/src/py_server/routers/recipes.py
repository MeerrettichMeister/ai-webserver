"""Routes for recipes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from py_server.db import SessionDep
from py_server.dto import (
    Page,
    RecipeCreate,
    RecipeListQuery,
    RecipeRead,
    RecipeReplace,
    RecipeSummary,
    RecipeUpdate,
)
from py_server.etags import PRECONDITION_RESPONSES, IfMatchDep, etag
from py_server.service import RecipeService

router = APIRouter(prefix="/recipes", tags=["recipes"])


def get_recipe_service(session: SessionDep) -> RecipeService:
    """Dependency: the recipe service on the request's session."""
    return RecipeService(session)


RecipeServiceDep = Annotated[RecipeService, Depends(get_recipe_service)]


@router.get("")
def list_recipes(
    query: Annotated[RecipeListQuery, Query()], service: RecipeServiceDep
) -> Page[RecipeSummary]:
    """One page of the recipes, ordered by name."""
    return service.find_page(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeCreate, service: RecipeServiceDep) -> RecipeRead:
    """Create a recipe with its ingredients and steps."""
    return service.create(payload)


@router.get("/{recipe_id}")
def get_recipe(recipe_id: UUID, service: RecipeServiceDep, response: Response) -> RecipeRead:
    """One recipe with ingredients and steps; its version is sent as ETag."""
    recipe = service.get(recipe_id)
    response.headers["ETag"] = etag(recipe.version)
    return recipe


@router.put("/{recipe_id}", responses=PRECONDITION_RESPONSES)
def replace_recipe(
    recipe_id: UUID,
    payload: RecipeReplace,
    if_match: IfMatchDep,
    service: RecipeServiceDep,
    response: Response,
) -> RecipeRead:
    """Replace the whole recipe in one go.

    Ingredients and steps with an `id` are updated, those without one are added, and the
    recipe's existing ones that are left out are deleted. Steps are renumbered in list order.
    """
    recipe = service.replace(recipe_id, payload, if_match)
    response.headers["ETag"] = etag(recipe.version)
    return recipe


@router.patch("/{recipe_id}", responses=PRECONDITION_RESPONSES)
def update_recipe(
    recipe_id: UUID,
    payload: RecipeUpdate,
    if_match: IfMatchDep,
    service: RecipeServiceDep,
    response: Response,
) -> RecipeRead:
    """Rename a recipe; requires If-Match with its current version."""
    recipe = service.update(recipe_id, payload, if_match)
    response.headers["ETag"] = etag(recipe.version)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: UUID, service: RecipeServiceDep) -> None:
    """Delete a recipe with its ingredients and steps."""
    service.delete(recipe_id)
