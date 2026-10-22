"""Request and response bodies for a recipe's details."""

from pydantic import BaseModel, ConfigDict, Field

from py_server.model import Difficulty


class RecipeDetailsFields(BaseModel):
    """Servings, total time and difficulty of a recipe."""

    servings: int = Field(ge=1, le=1000, description="Number of portions the recipe makes.")
    preparation_time_minutes: int = Field(
        ge=1, le=10_000, description="Total time from start to serving, in minutes."
    )
    difficulty: Difficulty


class RecipeDetailsRead(RecipeDetailsFields):
    """A recipe's details as returned by the API."""

    model_config = ConfigDict(from_attributes=True)
