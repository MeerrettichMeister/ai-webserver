from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from py_server.model import Ingredient
from py_server.repository.base import Repository


class IngredientRepository(Repository):
    def get(self, recipe_id: UUID, ingredient_id: UUID) -> Ingredient | None:
        """The ingredient, if it belongs to the recipe."""
        return self.session.scalar(
            select(Ingredient).where(
                Ingredient.id == ingredient_id, Ingredient.recipe_id == recipe_id
            )
        )

    def find_by_recipe(self, recipe_id: UUID, search: str = "") -> Sequence[Ingredient]:
        """The recipe's ingredients by name, only those whose name contains `search` if given."""
        query = (
            select(Ingredient).where(Ingredient.recipe_id == recipe_id).order_by(Ingredient.name)
        )
        if search:
            # autoescape makes % and _ in the search text match literally.
            query = query.where(Ingredient.name.icontains(search, autoescape=True))
        return self.session.scalars(query).all()
