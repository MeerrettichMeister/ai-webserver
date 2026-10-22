import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from py_server.model.base import Base

if TYPE_CHECKING:
    from py_server.model.recipe import Recipe
    from py_server.model.step import Step


class Ingredient(Base):
    """An ingredient of one recipe, with the quantity that recipe needs."""

    __tablename__ = "ingredient"
    __table_args__ = (
        # Deferred to commit so a bulk update can swap names between ingredients.
        UniqueConstraint("recipe_id", "name", deferrable=True, initially="DEFERRED"),
        # Target for the composite FK on step.
        UniqueConstraint("recipe_id", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(50))
    # Bumped by SQLAlchemy on every UPDATE, which also checks it in the WHERE clause.
    version: Mapped[int] = mapped_column()

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012 (declared by DeclarativeBase)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    steps: Mapped[list[Step]] = relationship(back_populates="ingredient", overlaps="recipe,steps")
