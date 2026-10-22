from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from py_server.db import SessionDep
from py_server.etags import PRECONDITION_RESPONSES, IfMatchDep, check_if_match, commit_or_412, etag
from py_server.models import Ingredient, Recipe, Step
from py_server.schemas import StepRead, StepUpdate

router = APIRouter(prefix="/recipes/{recipe_id}/steps", tags=["steps"])


def get_step_or_404(recipe_id: UUID, step_id: UUID, session: SessionDep) -> Step:
    step = session.scalar(
        select(Step)
        .where(Step.id == step_id, Step.recipe_id == recipe_id)
        .options(selectinload(Step.ingredient))
    )
    if step is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Step not found")
    return step


StepDep = Annotated[Step, Depends(get_step_or_404)]


@router.get("")
def list_steps(recipe_id: UUID, session: SessionDep) -> list[StepRead]:
    if session.get(Recipe, recipe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe not found")
    query = (
        select(Step)
        .where(Step.recipe_id == recipe_id)
        .order_by(Step.position)
        .options(selectinload(Step.ingredient))
    )
    return [StepRead.model_validate(s) for s in session.scalars(query)]


@router.get("/{step_id}")
def get_step(step: StepDep, response: Response) -> StepRead:
    response.headers["ETag"] = etag(step.version)
    return StepRead.model_validate(step)


@router.put("/{step_id}", responses=PRECONDITION_RESPONSES)
def update_step(
    payload: StepUpdate,
    step: StepDep,
    if_match: IfMatchDep,
    session: SessionDep,
    response: Response,
) -> StepRead:
    check_if_match(if_match, step.version)
    ingredient = session.get(Ingredient, payload.ingredient_id)
    if ingredient is None or ingredient.recipe_id != step.recipe_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "The recipe has no ingredient with this id"
        )
    step.ingredient = ingredient
    step.preparation_method = payload.preparation_method
    step.recipe.touch()
    commit_or_412(session)
    response.headers["ETag"] = etag(step.version)
    return StepRead.model_validate(step)
