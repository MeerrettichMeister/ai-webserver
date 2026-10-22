from uuid import UUID

from pydantic import BaseModel, Field

from py_server.dto.common import OptionalId, ReadModel, Version


class IngredientFields(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: str = Field(max_length=50)
    unit: str = Field(max_length=50)


class IngredientCreate(IngredientFields):
    """An ingredient of a new recipe."""


class IngredientReplace(IngredientFields):
    """An ingredient of a replaced recipe: updated if it has an `id`, otherwise added."""

    id: OptionalId = None


class IngredientUpdate(IngredientFields):
    """The new state of one ingredient."""


class IngredientRead(ReadModel):
    id: UUID
    name: str
    amount: str
    unit: str
    version: Version
