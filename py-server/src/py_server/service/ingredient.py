from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from py_server.dto import IngredientRead, IngredientUpdate
from py_server.model import Ingredient
from py_server.repository import IngredientRepository, RecipeRepository
from py_server.service.errors import ConflictError, NotFoundError
from py_server.service.versioning import ExpectedVersion, commit


class IngredientService:
    """Use cases on single ingredients of a recipe; each public method is one transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._recipes = RecipeRepository(session)
        self._ingredients = IngredientRepository(session)

    def find_all(self, recipe_id: UUID, search: str = "") -> list[IngredientRead]:
        if not self._recipes.exists(recipe_id):
            raise NotFoundError("Recipe not found")
        ingredients = self._ingredients.find_by_recipe(recipe_id, search)
        return [IngredientRead.model_validate(i) for i in ingredients]

    def get(self, recipe_id: UUID, ingredient_id: UUID) -> IngredientRead:
        return IngredientRead.model_validate(self._get(recipe_id, ingredient_id))

    def update(
        self,
        recipe_id: UUID,
        ingredient_id: UUID,
        payload: IngredientUpdate,
        expected: ExpectedVersion,
    ) -> IngredientRead:
        ingredient = self._get(recipe_id, ingredient_id)
        expected.check(ingredient.version)
        ingredient.name = payload.ingredient
        ingredient.amount = payload.amount
        ingredient.unit = payload.unit
        ingredient.recipe.touch()
        try:
            commit(self._session)
        except IntegrityError as exc:
            self._session.rollback()
            msg = "The recipe already has an ingredient with this name"
            raise ConflictError(msg) from exc
        return IngredientRead.model_validate(ingredient)

    def _get(self, recipe_id: UUID, ingredient_id: UUID) -> Ingredient:
        ingredient = self._ingredients.get(recipe_id, ingredient_id)
        if ingredient is None:
            raise NotFoundError("Ingredient not found")
        return ingredient
