"""SQLAlchemy ORM models, one module per table.

Importing this package registers every table on `Base.metadata`, which the mappers (to resolve
relationships between modules) and Alembic's autogenerate rely on.
"""

from py_server.model.base import Base
from py_server.model.ingredient import Ingredient
from py_server.model.recipe import Recipe
from py_server.model.recipe_details import Difficulty, RecipeDetails
from py_server.model.step import Step

__all__ = ["Base", "Difficulty", "Ingredient", "Recipe", "RecipeDetails", "Step"]
