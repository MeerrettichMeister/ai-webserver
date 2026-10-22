"""Pydantic request and response bodies (DTOs) of the API, one module per resource.

`*Create`, `*Replace` and `*Update` are request bodies; `*Read` are response bodies.
"""

from py_server.dto.ingredient import (
    IngredientCreate,
    IngredientRead,
    IngredientReplace,
    IngredientUpdate,
)
from py_server.dto.recipe import RecipeCreate, RecipeRead, RecipeReplace, RecipeUpdate
from py_server.dto.step import StepCreate, StepRead, StepReplace, StepUpdate

__all__ = [
    "IngredientCreate",
    "IngredientRead",
    "IngredientReplace",
    "IngredientUpdate",
    "RecipeCreate",
    "RecipeRead",
    "RecipeReplace",
    "RecipeUpdate",
    "StepCreate",
    "StepRead",
    "StepReplace",
    "StepUpdate",
]
