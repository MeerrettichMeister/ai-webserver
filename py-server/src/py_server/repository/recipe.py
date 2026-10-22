from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from py_server.model import Recipe
from py_server.repository.base import Repository


class RecipeRepository(Repository):
    def get(self, recipe_id: UUID) -> Recipe | None:
        """The recipe with its ingredients and steps loaded, or None."""
        return self.session.scalar(self._query().where(Recipe.id == recipe_id))

    def exists(self, recipe_id: UUID) -> bool:
        return self.session.get(Recipe, recipe_id) is not None

    def find_all(self, search: str = "") -> Sequence[Recipe]:
        """Recipes by name, only those whose name contains `search` (ignoring case) if given."""
        query = self._query().order_by(Recipe.name)
        if search:
            # autoescape makes % and _ in the search text match literally.
            query = query.where(Recipe.name.icontains(search, autoescape=True))
        return self.session.scalars(query).all()

    def add(self, recipe: Recipe) -> None:
        self.session.add(recipe)

    def delete(self, recipe: Recipe) -> None:
        self.session.delete(recipe)

    @staticmethod
    def _query() -> Select[Recipe]:
        """Select recipes with their ingredients and steps loaded up front."""
        return select(Recipe).options(selectinload(Recipe.ingredients), selectinload(Recipe.steps))
