import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from py_server.model.base import Base

if TYPE_CHECKING:
    from py_server.model.ingredient import Ingredient
    from py_server.model.recipe import Recipe


class Step(Base):
    """One step of a recipe: what to do with which of the recipe's ingredients.

    (recipe_id, position) is unique, and the same ingredient can appear in several steps.
    The FK on (recipe_id, ingredient_id) guarantees the ingredient belongs to the same recipe.
    """

    __tablename__ = "step"
    __table_args__ = (
        # Deferred to commit so a bulk update can reorder steps.
        UniqueConstraint("recipe_id", "position", deferrable=True, initially="DEFERRED"),
        ForeignKeyConstraint(
            ["recipe_id", "ingredient_id"],
            ["ingredient.recipe_id", "ingredient.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column()
    ingredient_id: Mapped[uuid.UUID] = mapped_column(index=True)
    preparation_method: Mapped[str] = mapped_column(String(1000))
    # Bumped by SQLAlchemy on every UPDATE, which also checks it in the WHERE clause.
    version: Mapped[int] = mapped_column()

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012 (declared by DeclarativeBase)

    recipe: Mapped[Recipe] = relationship(back_populates="steps", overlaps="steps")
    ingredient: Mapped[Ingredient] = relationship(back_populates="steps", overlaps="recipe,steps")
