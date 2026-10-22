"""Routes for the steps of a recipe."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from py_server.db import SessionDep
from py_server.dto import StepRead, StepUpdate
from py_server.etags import PRECONDITION_RESPONSES, IfMatchDep, etag
from py_server.service import StepService

router = APIRouter(prefix="/recipes/{recipe_id}/steps", tags=["steps"])


def get_step_service(session: SessionDep) -> StepService:
    """Dependency: the step service on the request's session."""
    return StepService(session)


StepServiceDep = Annotated[StepService, Depends(get_step_service)]


@router.get("")
def list_steps(recipe_id: UUID, service: StepServiceDep) -> list[StepRead]:
    """The recipe's steps in order."""
    return service.find_all(recipe_id)


@router.get("/{step_id}")
def get_step(
    recipe_id: UUID, step_id: UUID, service: StepServiceDep, response: Response
) -> StepRead:
    """One step; its version is sent as ETag."""
    step = service.get(recipe_id, step_id)
    response.headers["ETag"] = etag(step.version)
    return step


@router.put("/{step_id}", responses=PRECONDITION_RESPONSES)
def update_step(
    recipe_id: UUID,
    step_id: UUID,
    payload: StepUpdate,
    if_match: IfMatchDep,
    service: StepServiceDep,
    response: Response,
) -> StepRead:
    """Change one step's text; requires If-Match with its current version."""
    step = service.update(recipe_id, step_id, payload, if_match)
    response.headers["ETag"] = etag(step.version)
    return step
