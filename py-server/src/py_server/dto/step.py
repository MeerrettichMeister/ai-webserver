"""Request and response bodies for steps."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from py_server.dto.common import OptionalId, ReadModel, Version

# The instruction of one step.
StepText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
    Field(description="What to do in this step."),
]


class StepReplace(BaseModel):
    """A step of a replaced recipe: updated if it has an `id`, otherwise added."""

    id: OptionalId = None
    preparation_method: StepText


class StepUpdate(BaseModel):
    """The new state of one step."""

    preparation_method: StepText


class StepRead(ReadModel):
    """A step with its id, position and version."""

    id: UUID
    position: int
    preparation_method: str
    version: Version
