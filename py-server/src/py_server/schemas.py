from collections.abc import Sequence
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema

# An id that may be left out; documented as a plain (not nullable) uuid.
OptionalId = Annotated[
    UUID | SkipJsonSchema[None],
    Field(description="Id of the existing item to update; leave out to add a new one."),
]


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: str = Field(max_length=50)
    unit: str = Field(max_length=50)


class IngredientReplace(IngredientCreate):
    id: OptionalId = None


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    amount: str
    unit: str
    version: int = Field(description='Send as `If-Match: "<version>"` when updating.')


class StepCreate(BaseModel):
    ingredient: str = Field(description="Name of one of the recipe's `ingredients`.")
    preparation_method: str = Field(max_length=1000)


class StepReplace(StepCreate):
    id: OptionalId = None


class StepUpdate(BaseModel):
    ingredient_id: UUID = Field(description="Id of one of the recipe's ingredients.")
    preparation_method: str = Field(max_length=1000)


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    ingredient: IngredientRead
    preparation_method: str
    version: int = Field(description='Send as `If-Match: "<version>"` when updating.')


def _check_ingredient_names(
    ingredients: Sequence[IngredientCreate], steps: Sequence[StepCreate]
) -> None:
    names = [ingredient.name for ingredient in ingredients]
    if duplicates := {name for name in names if names.count(name) > 1}:
        msg = f"Duplicate ingredient names: {', '.join(sorted(duplicates))}"
        raise ValueError(msg)
    if unknown := {step.ingredient for step in steps} - set(names):
        msg = f"Steps reference unknown ingredients: {', '.join(sorted(unknown))}"
        raise ValueError(msg)


def _check_unique_ids(items: Sequence[IngredientReplace] | Sequence[StepReplace]) -> None:
    ids = [item.id for item in items if item.id is not None]
    if duplicates := {i for i in ids if ids.count(i) > 1}:
        msg = f"Duplicate ids: {', '.join(sorted(map(str, duplicates)))}"
        raise ValueError(msg)


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    ingredients: list[IngredientCreate] = Field(default_factory=list)
    steps: list[StepCreate] = Field(
        default_factory=list, description="Steps in the order they are performed."
    )

    @model_validator(mode="after")
    def check_ingredient_names(self) -> Self:
        _check_ingredient_names(self.ingredients, self.steps)
        return self


class RecipeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RecipeReplace(BaseModel):
    """The complete recipe: ingredients and steps left out are deleted."""

    name: str = Field(min_length=1, max_length=255)
    ingredients: list[IngredientReplace] = Field(default_factory=list)
    steps: list[StepReplace] = Field(
        default_factory=list, description="Steps in the order they are performed."
    )

    @model_validator(mode="after")
    def check_references(self) -> Self:
        _check_ingredient_names(self.ingredients, self.steps)
        _check_unique_ids(self.ingredients)
        _check_unique_ids(self.steps)
        return self


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    version: int = Field(description='Send as `If-Match: "<version>"` when updating.')
    ingredients: list[IngredientRead]
    steps: list[StepRead]
