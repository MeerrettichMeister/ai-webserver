from collections.abc import Iterable, Mapping
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from py_server.db import SessionDep
from py_server.dto import RecipeCreate, RecipeRead, RecipeReplace, RecipeUpdate
from py_server.etags import (
    PRECONDITION_RESPONSES,
    IfMatchDep,
    check_if_match,
    commit_or_412,
    etag,
)
from py_server.model import Ingredient, Recipe, Step

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _recipe_query() -> Select[Recipe]:
    """Select recipes with their ingredients and steps loaded up front."""
    return select(Recipe).options(selectinload(Recipe.ingredients), selectinload(Recipe.steps))


def get_recipe_or_404(recipe_id: UUID, session: SessionDep) -> Recipe:
    recipe = session.scalar(_recipe_query().where(Recipe.id == recipe_id))
    if recipe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
    return recipe


RecipeDep = Annotated[Recipe, Depends(get_recipe_or_404)]


@router.get("")
def list_recipes(
    session: SessionDep,
    search: Annotated[
        str, Query(description="Only recipes whose name contains this, ignoring case.")
    ] = "",
) -> list[RecipeRead]:
    query = _recipe_query().order_by(Recipe.name)
    if search:
        # autoescape makes % and _ in the search text match literally.
        query = query.where(Recipe.name.icontains(search, autoescape=True))
    return [RecipeRead.model_validate(r) for r in session.scalars(query)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeCreate, session: SessionDep) -> RecipeRead:
    recipe = Recipe(
        name=payload.name,
        ingredients=[
            Ingredient(name=i.ingredient, amount=i.amount, unit=i.unit) for i in payload.ingredients
        ],
        steps=[
            Step(position=position, preparation_method=text)
            for position, text in enumerate(payload.steps, start=1)
        ],
    )
    session.add(recipe)
    session.commit()
    return RecipeRead.model_validate(get_recipe_or_404(recipe.id, session))


@router.get("/{recipe_id}")
def get_recipe(recipe: RecipeDep, response: Response) -> RecipeRead:
    response.headers["ETag"] = etag(recipe.version)
    return RecipeRead.model_validate(recipe)


@router.put("/{recipe_id}", responses=PRECONDITION_RESPONSES)
def replace_recipe(
    payload: RecipeReplace,
    recipe: RecipeDep,
    if_match: IfMatchDep,
    session: SessionDep,
    response: Response,
) -> RecipeRead:
    """Replace the whole recipe in one go.

    Ingredients and steps with an `id` are updated, those without one are added, and the
    recipe's existing ones that are left out are deleted. Steps are renumbered in list order.
    """
    check_if_match(if_match, recipe.version)
    existing_ingredients = {i.id: i for i in recipe.ingredients}
    existing_steps = {s.id: s for s in recipe.steps}
    _require_known_ids("ingredient", (i.id for i in payload.ingredients), existing_ingredients)
    _require_known_ids("step", (s.id for s in payload.steps), existing_steps)

    ingredients: list[Ingredient] = []
    for item in payload.ingredients:
        ingredient = existing_ingredients[item.id] if item.id else Ingredient()
        ingredient.name = item.ingredient
        ingredient.amount = item.amount
        ingredient.unit = item.unit
        ingredients.append(ingredient)

    steps: list[Step] = []
    for position, item in enumerate(payload.steps, start=1):
        step = existing_steps[item.id] if item.id else Step()
        step.position = position
        step.preparation_method = item.preparation_method
        steps.append(step)

    recipe.name = payload.name
    recipe.ingredients = ingredients
    recipe.steps = steps
    recipe.touch()
    commit_or_412(session)
    response.headers["ETag"] = etag(recipe.version)
    return RecipeRead.model_validate(get_recipe_or_404(recipe.id, session))


def _require_known_ids(
    kind: str, ids: Iterable[UUID | None], existing: Mapping[UUID, object]
) -> None:
    if unknown := {i for i in ids if i is not None and i not in existing}:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Not {kind}s of this recipe: {', '.join(sorted(map(str, unknown)))}",
        )


@router.patch("/{recipe_id}", responses=PRECONDITION_RESPONSES)
def update_recipe(
    payload: RecipeUpdate,
    recipe: RecipeDep,
    if_match: IfMatchDep,
    session: SessionDep,
    response: Response,
) -> RecipeRead:
    check_if_match(if_match, recipe.version)
    recipe.name = payload.name
    recipe.touch()
    commit_or_412(session)
    response.headers["ETag"] = etag(recipe.version)
    return RecipeRead.model_validate(get_recipe_or_404(recipe.id, session))


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe: RecipeDep, session: SessionDep) -> None:
    session.delete(recipe)
    session.commit()
