from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from py_server.db import SessionDep
from py_server.etags import (
    PRECONDITION_RESPONSES,
    IfMatchDep,
    check_if_match,
    etag,
    precondition_failed,
)
from py_server.models import Ingredient, Recipe
from py_server.schemas import IngredientCreate, IngredientRead

router = APIRouter(prefix="/recipes/{recipe_id}/ingredients", tags=["ingredients"])


def get_ingredient_or_404(recipe_id: UUID, ingredient_id: UUID, session: SessionDep) -> Ingredient:
    ingredient = session.scalar(
        select(Ingredient).where(Ingredient.id == ingredient_id, Ingredient.recipe_id == recipe_id)
    )
    if ingredient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ingredient not found")
    return ingredient


IngredientDep = Annotated[Ingredient, Depends(get_ingredient_or_404)]


@router.get("")
def list_ingredients(
    recipe_id: UUID,
    session: SessionDep,
    search: Annotated[
        str, Query(description="Only ingredients whose name contains this, ignoring case.")
    ] = "",
) -> list[IngredientRead]:
    if session.get(Recipe, recipe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
    query = select(Ingredient).where(Ingredient.recipe_id == recipe_id).order_by(Ingredient.name)
    if search:
        # autoescape makes % and _ in the search text match literally.
        query = query.where(Ingredient.name.icontains(search, autoescape=True))
    return [IngredientRead.model_validate(i) for i in session.scalars(query)]


@router.get("/{ingredient_id}")
def get_ingredient(ingredient: IngredientDep, response: Response) -> IngredientRead:
    response.headers["ETag"] = etag(ingredient.version)
    return IngredientRead.model_validate(ingredient)


@router.put(
    "/{ingredient_id}",
    responses={
        **PRECONDITION_RESPONSES,
        status.HTTP_409_CONFLICT: {"description": "Another ingredient has this name"},
    },
)
def update_ingredient(
    payload: IngredientCreate,
    ingredient: IngredientDep,
    if_match: IfMatchDep,
    session: SessionDep,
    response: Response,
) -> IngredientRead:
    check_if_match(if_match, ingredient.version)
    ingredient.name = payload.name
    ingredient.amount = payload.amount
    ingredient.unit = payload.unit
    ingredient.recipe.touch()
    try:
        session.commit()
    except StaleDataError as exc:
        # Someone committed a new version between our read and our UPDATE.
        session.rollback()
        raise precondition_failed() from exc
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The recipe already has an ingredient with this name"
        ) from exc
    response.headers["ETag"] = etag(ingredient.version)
    return IngredientRead.model_validate(ingredient)
