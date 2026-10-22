"""ORM model of the recipe_details table, 1:1 with recipe."""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from py_server.model.base import Base

if TYPE_CHECKING:
    from py_server.model.recipe import Recipe


class Difficulty(StrEnum):
    """How hard a recipe is to make."""

    easy = "easy"
    medium = "medium"
    hard = "hard"


class RecipeDetails(Base):
    """Facts about one recipe: servings, total time and difficulty."""

    __tablename__ = "recipe_details"

    # Primary key and foreign key at once, so a recipe has at most one row (1:1).
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    servings: Mapped[int] = mapped_column()
    preparation_time_minutes: Mapped[int] = mapped_column()
    # Stored as text with a CHECK constraint instead of a PostgreSQL enum type.
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False, create_constraint=True, length=10)
    )

    recipe: Mapped[Recipe] = relationship(back_populates="details")
