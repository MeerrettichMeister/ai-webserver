"""ORM model of the step table."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from py_server.model.base import Base

if TYPE_CHECKING:
    from py_server.model.recipe import Recipe


class Step(Base):
    """One step of a recipe: an instruction in plain text, at its position in the recipe."""

    __tablename__ = "step"
    __table_args__ = (
        # Deferred to commit so a bulk update can reorder steps.
        UniqueConstraint("recipe_id", "position", deferrable=True, initially="DEFERRED"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column()
    preparation_method: Mapped[str] = mapped_column(String(1000))
    # Bumped by SQLAlchemy on every UPDATE, which also checks it in the WHERE clause.
    version: Mapped[int] = mapped_column()

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012 (declared by DeclarativeBase)

    recipe: Mapped[Recipe] = relationship(back_populates="steps")
