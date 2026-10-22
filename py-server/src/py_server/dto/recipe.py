from collections.abc import Sequence
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from py_server.dto.common import ReadModel, Version
from py_server.dto.ingredient import (
    IngredientCreate,
    IngredientFields,
    IngredientRead,
    IngredientReplace,
)
from py_server.dto.pagination import PageParams
from py_server.dto.step import StepRead, StepReplace, StepText


def _check_unique_names(ingredients: Sequence[IngredientFields]) -> None:
    names = [ingredient.ingredient for ingredient in ingredients]
    if duplicates := {name for name in names if names.count(name) > 1}:
        msg = f"Duplicate ingredient names: {', '.join(sorted(duplicates))}"
        raise ValueError(msg)


def _check_unique_ids(items: Sequence[IngredientReplace] | Sequence[StepReplace]) -> None:
    ids = [item.id for item in items if item.id is not None]
    if duplicates := {i for i in ids if ids.count(i) > 1}:
        msg = f"Duplicate ids: {', '.join(sorted(map(str, duplicates)))}"
        raise ValueError(msg)


class RecipeListQuery(PageParams):
    """Query parameters of the recipe list: which recipes, and which page of them."""

    search: str = Field(
        default="", description="Only recipes whose name contains this, ignoring case."
    )


class RecipeCreate(BaseModel):
    """A new recipe; the seed recipe `seed/Pfannkuchen.json` is an example."""

    name: str = Field(min_length=1, max_length=255)
    ingredients: list[IngredientCreate] = Field(default_factory=list)
    steps: list[StepText] = Field(
        default_factory=list, description="Instructions in the order they are performed."
    )

    @model_validator(mode="after")
    def check_ingredient_names(self) -> Self:
        _check_unique_names(self.ingredients)
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
        _check_unique_names(self.ingredients)
        _check_unique_ids(self.ingredients)
        _check_unique_ids(self.steps)
        return self


class RecipeRead(ReadModel):
    id: UUID
    name: str
    version: Version
    ingredients: list[IngredientRead]
    steps: list[StepRead]
