"""Business logic for steps."""

from uuid import UUID

from sqlalchemy.orm import Session

from py_server.dto import StepRead, StepUpdate
from py_server.model import Step
from py_server.repository import RecipeRepository, StepRepository
from py_server.service.errors import NotFoundError
from py_server.service.versioning import ExpectedVersion, commit


class StepService:
    """Use cases on single steps of a recipe; each public method is one transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._recipes = RecipeRepository(session)
        self._steps = StepRepository(session)

    def find_all(self, recipe_id: UUID) -> list[StepRead]:
        """The recipe's steps in order."""
        if not self._recipes.exists(recipe_id):
            raise NotFoundError("Recipe not found")
        return [StepRead.model_validate(s) for s in self._steps.find_by_recipe(recipe_id)]

    def get(self, recipe_id: UUID, step_id: UUID) -> StepRead:
        """One step of the recipe."""
        return StepRead.model_validate(self._get(recipe_id, step_id))

    def update(
        self, recipe_id: UUID, step_id: UUID, payload: StepUpdate, expected: ExpectedVersion
    ) -> StepRead:
        """Change a step's text if `expected` matches its version."""
        step = self._get(recipe_id, step_id)
        expected.check(step.version)
        step.preparation_method = payload.preparation_method
        step.recipe.touch()
        commit(self._session)
        return StepRead.model_validate(step)

    def _get(self, recipe_id: UUID, step_id: UUID) -> Step:
        """Load the step of the recipe, or raise NotFoundError."""
        step = self._steps.get(recipe_id, step_id)
        if step is None:
            raise NotFoundError("Step not found")
        return step
