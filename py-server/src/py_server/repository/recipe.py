"""Database queries for recipes."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload, selectinload

from py_server.model import Recipe
from py_server.repository.base import Repository


class RecipeRepository(Repository):
    """Data access for the recipe table."""

    def get(self, recipe_id: UUID) -> Recipe | None:
        """The recipe with its details, ingredients and steps loaded, or None."""
        return self.session.scalar(self._query().where(Recipe.id == recipe_id))

    def exists(self, recipe_id: UUID) -> bool:
        """Whether a recipe with this id exists."""
        return self.session.get(Recipe, recipe_id) is not None

    def find_page(self, search: str, offset: int, limit: int) -> Sequence[Recipe]:
        """Up to `limit` recipes after the first `offset`, ordered by name (see _matching).

        Only the recipe rows: ingredients and steps are not loaded.
        """
        # id breaks ties between equal names, so pages neither overlap nor skip recipes.
        query = (
            _matching(select(Recipe), search)
            .order_by(Recipe.name, Recipe.id)
            .offset(offset)
            .limit(limit)
        )
        return self.session.scalars(query).all()

    def count(self, search: str) -> int:
        """Number of recipes find_page() pages through."""
        return self.session.scalar(_matching(select(func.count()).select_from(Recipe), search)) or 0

    def add(self, recipe: Recipe) -> None:
        """Stage a new recipe, with its ingredients and steps, for insert."""
        self.session.add(recipe)

    def delete(self, recipe: Recipe) -> None:
        """Stage a recipe for deletion; its ingredients and steps cascade."""
        self.session.delete(recipe)

    @staticmethod
    def _query() -> Select[Recipe]:
        """Select recipes with their details, ingredients and steps loaded up front."""
        # The 1:1 details come in the same query (JOIN); the lists in one query each.
        return select(Recipe).options(
            joinedload(Recipe.details),
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
        )


def _matching[*Ts](query: Select[*Ts], search: str) -> Select[*Ts]:
    """Only recipes whose name contains `search` (ignoring case), if given."""
    if not search:
        return query
    # autoescape makes % and _ in the search text match literally.
    return query.where(Recipe.name.icontains(search, autoescape=True))
