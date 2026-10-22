"""Recipes that are always available: the app creates any that are missing on startup.

Each seed recipe is a `POST /recipes` body in this package with a fixed id, so startup can tell
whether it exists. Existing seed recipes are left as they are, also if they were edited; deleted
ones come back on the next start.
"""

from contextlib import suppress
from importlib.resources import files
from uuid import UUID

from sqlalchemy.orm import Session

from py_server.dto import RecipeCreate
from py_server.service import ConflictError, RecipeService

SEED_RECIPES: dict[UUID, str] = {
    UUID("44a67d4d-b723-4adb-b877-193a1fc07698"): "Pfannkuchen.json",
}


def seed_recipes(session: Session) -> None:
    """Create the seed recipes that do not exist yet."""
    service = RecipeService(session)
    for recipe_id, file_name in SEED_RECIPES.items():
        if service.exists(recipe_id):
            continue
        payload = RecipeCreate.model_validate_json(files(__name__).joinpath(file_name).read_bytes())
        # ConflictError: another instance of the app created it at the same time.
        with suppress(ConflictError):
            service.create(payload, recipe_id=recipe_id)
