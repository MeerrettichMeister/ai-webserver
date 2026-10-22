"""Pydantic request and response bodies (DTOs) of the API, one module per resource.

`*Create`, `*Replace` and `*Update` are request bodies; `*Read` are response bodies.
"""

from py_server.dto.ingredient import (
    IngredientCreate,
    IngredientRead,
    IngredientReplace,
    IngredientUpdate,
)
from py_server.dto.pagination import Page, PageParams
from py_server.dto.recipe import (
    RecipeCreate,
    RecipeListQuery,
    RecipeRead,
    RecipeReplace,
    RecipeSummary,
    RecipeUpdate,
)
from py_server.dto.recipe_details import RecipeDetailsFields, RecipeDetailsRead
from py_server.dto.step import StepRead, StepReplace, StepUpdate

__all__ = [
    "IngredientCreate",
    "IngredientRead",
    "IngredientReplace",
    "IngredientUpdate",
    "Page",
    "PageParams",
    "RecipeCreate",
    "RecipeDetailsFields",
    "RecipeDetailsRead",
    "RecipeListQuery",
    "RecipeRead",
    "RecipeReplace",
    "RecipeSummary",
    "RecipeUpdate",
    "StepRead",
    "StepReplace",
    "StepUpdate",
]
