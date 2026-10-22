"""ORM model of the recipe table."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from py_server.model.base import Base

if TYPE_CHECKING:
    from py_server.model.ingredient import Ingredient
    from py_server.model.step import Step


class Recipe(Base):
    """A recipe; owns its ingredients and steps."""

    __tablename__ = "recipe"
    __table_args__ = (
        # The order of the paginated list, so a page is read from the index instead of sorting
        # every recipe; id breaks ties between equal names.
        Index("ix_recipe_name_id", "name", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    # Versions the whole recipe including its ingredients and steps, so it is bumped by hand
    # (see touch()); SQLAlchemy still checks the old value in the UPDATE's WHERE clause.
    version: Mapped[int] = mapped_column(default=1)

    __mapper_args__ = {  # noqa: RUF012 (declared by DeclarativeBase)
        "version_id_col": version,
        "version_id_generator": False,
    }

    ingredients: Mapped[list[Ingredient]] = relationship(
        back_populates="recipe",
        order_by="Ingredient.name",
        cascade="all, delete-orphan",
    )
    steps: Mapped[list[Step]] = relationship(
        back_populates="recipe",
        order_by="Step.position",
        cascade="all, delete-orphan",
    )

    def touch(self) -> None:
        """Record that the recipe, or one of its ingredients or steps, has changed."""
        self.version += 1
