from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from py_server.model import Step
from py_server.repository.base import Repository


class StepRepository(Repository):
    def get(self, recipe_id: UUID, step_id: UUID) -> Step | None:
        """The step, if it belongs to the recipe."""
        return self.session.scalar(
            select(Step).where(Step.id == step_id, Step.recipe_id == recipe_id)
        )

    def find_by_recipe(self, recipe_id: UUID) -> Sequence[Step]:
        """The recipe's steps in order."""
        query = select(Step).where(Step.recipe_id == recipe_id).order_by(Step.position)
        return self.session.scalars(query).all()
