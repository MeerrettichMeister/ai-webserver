import uuid

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipe"

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
        overlaps="steps",
    )

    def touch(self) -> None:
        """Record that the recipe, or one of its ingredients or steps, has changed."""
        self.version += 1


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
