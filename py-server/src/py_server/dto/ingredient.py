from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field

from py_server.dto.common import Amount, OptionalId, ReadModel, Version


class IngredientFields(BaseModel):
    ingredient: str = Field(min_length=1, max_length=255, description="Name of the ingredient.")
    amount: Amount
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
    # Read from Ingredient.name; "ingredient" too, as FastAPI validates the response body again.
    ingredient: str = Field(validation_alias=AliasChoices("name", "ingredient"))
    amount: Amount
    unit: str
    version: Version
