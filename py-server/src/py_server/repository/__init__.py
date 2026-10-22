"""Data access: one repository per table, used by the services."""

from py_server.repository.ingredient import IngredientRepository
from py_server.repository.recipe import RecipeRepository
from py_server.repository.step import StepRepository

__all__ = ["IngredientRepository", "RecipeRepository", "StepRepository"]
