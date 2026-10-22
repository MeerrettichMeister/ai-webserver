from collections.abc import Iterable, Mapping
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from py_server.dto import (
    Page,
    RecipeCreate,
    RecipeListQuery,
    RecipeRead,
    RecipeReplace,
    RecipeUpdate,
)
from py_server.model import Ingredient, Recipe, Step
from py_server.repository import RecipeRepository
from py_server.service.errors import ConflictError, InvalidReferenceError, NotFoundError
from py_server.service.versioning import ExpectedVersion, commit


class RecipeService:
    """Use cases on whole recipes; each public method is one transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._recipes = RecipeRepository(session)

    def find_page(self, query: RecipeListQuery) -> Page[RecipeRead]:
        recipes = self._recipes.find_page(query.search, offset=query.offset, limit=query.size)
        return Page[RecipeRead](
            items=[RecipeRead.model_validate(r) for r in recipes],
            total=self._recipes.count(query.search),
            page=query.page,
            size=query.size,
        )

    def get(self, recipe_id: UUID) -> RecipeRead:
        return RecipeRead.model_validate(self._get(recipe_id))

    def exists(self, recipe_id: UUID) -> bool:
        return self._recipes.exists(recipe_id)

    def create(self, payload: RecipeCreate, recipe_id: UUID | None = None) -> RecipeRead:
        """Create a recipe, with a new id unless `recipe_id` is given (as for seed recipes)."""
        recipe = Recipe(
            name=payload.name,
            ingredients=[
                Ingredient(name=i.ingredient, amount=i.amount, unit=i.unit)
                for i in payload.ingredients
            ],
            steps=[
                Step(position=position, preparation_method=text)
                for position, text in enumerate(payload.steps, start=1)
            ],
        )
        if recipe_id is not None:
            recipe.id = recipe_id
        self._recipes.add(recipe)
        try:
            commit(self._session)
        except IntegrityError as exc:
            self._session.rollback()
            msg = "A recipe with this id already exists"
            raise ConflictError(msg) from exc
        return self.get(recipe.id)

    def replace(
        self, recipe_id: UUID, payload: RecipeReplace, expected: ExpectedVersion
    ) -> RecipeRead:
        """Replace name, ingredients and steps.

        Items with an `id` are updated, those without one are added, and the recipe's existing
        ones that are left out are deleted. Steps are renumbered in list order.
        """
        recipe = self._get(recipe_id)
        expected.check(recipe.version)
        existing_ingredients = {i.id: i for i in recipe.ingredients}
        existing_steps = {s.id: s for s in recipe.steps}
        _require_known_ids("ingredient", (i.id for i in payload.ingredients), existing_ingredients)
        _require_known_ids("step", (s.id for s in payload.steps), existing_steps)

        ingredients: list[Ingredient] = []
        for item in payload.ingredients:
            ingredient = existing_ingredients[item.id] if item.id else Ingredient()
            ingredient.name = item.ingredient
            ingredient.amount = item.amount
            ingredient.unit = item.unit
            ingredients.append(ingredient)

        steps: list[Step] = []
        for position, item in enumerate(payload.steps, start=1):
            step = existing_steps[item.id] if item.id else Step()
            step.position = position
            step.preparation_method = item.preparation_method
            steps.append(step)

        recipe.name = payload.name
        recipe.ingredients = ingredients
        recipe.steps = steps
        recipe.touch()
        commit(self._session)
        return self.get(recipe.id)

    def update(
        self, recipe_id: UUID, payload: RecipeUpdate, expected: ExpectedVersion
    ) -> RecipeRead:
        recipe = self._get(recipe_id)
        expected.check(recipe.version)
        recipe.name = payload.name
        recipe.touch()
        commit(self._session)
        return self.get(recipe.id)

    def delete(self, recipe_id: UUID) -> None:
        self._recipes.delete(self._get(recipe_id))
        commit(self._session)

    def _get(self, recipe_id: UUID) -> Recipe:
        recipe = self._recipes.get(recipe_id)
        if recipe is None:
            raise NotFoundError("Recipe not found")
        return recipe


def _require_known_ids(
    kind: str, ids: Iterable[UUID | None], existing: Mapping[UUID, object]
) -> None:
    if unknown := {i for i in ids if i is not None and i not in existing}:
        msg = f"Not {kind}s of this recipe: {', '.join(sorted(map(str, unknown)))}"
        raise InvalidReferenceError(msg)
