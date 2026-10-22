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
    RecipeUpdate,
)
from py_server.etags import PRECONDITION_RESPONSES, IfMatchDep, etag
from py_server.service import RecipeService

router = APIRouter(prefix="/recipes", tags=["recipes"])


def get_recipe_service(session: SessionDep) -> RecipeService:
    return RecipeService(session)


RecipeServiceDep = Annotated[RecipeService, Depends(get_recipe_service)]


@router.get("")
def list_recipes(
    query: Annotated[RecipeListQuery, Query()], service: RecipeServiceDep
) -> Page[RecipeRead]:
    """One page of the recipes, ordered by name."""
    return service.find_page(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeCreate, service: RecipeServiceDep) -> RecipeRead:
    return service.create(payload)


@router.get("/{recipe_id}")
def get_recipe(recipe_id: UUID, service: RecipeServiceDep, response: Response) -> RecipeRead:
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
    recipe = service.update(recipe_id, payload, if_match)
    response.headers["ETag"] = etag(recipe.version)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: UUID, service: RecipeServiceDep) -> None:
    service.delete(recipe_id)
