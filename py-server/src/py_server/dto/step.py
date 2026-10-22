from uuid import UUID

from pydantic import BaseModel, Field

from py_server.dto.common import OptionalId, ReadModel, Version
from py_server.dto.ingredient import IngredientRead


class StepCreate(BaseModel):
    """A step of a new recipe."""

    ingredient: str = Field(description="Name of one of the recipe's `ingredients`.")
    preparation_method: str = Field(max_length=1000)


class StepReplace(StepCreate):
    """A step of a replaced recipe: updated if it has an `id`, otherwise added."""

    id: OptionalId = None


class StepUpdate(BaseModel):
    """The new state of one step."""

    ingredient_id: UUID = Field(description="Id of one of the recipe's ingredients.")
    preparation_method: str = Field(max_length=1000)


class StepRead(ReadModel):
    id: UUID
    position: int
    ingredient: IngredientRead
    preparation_method: str
    version: Version
