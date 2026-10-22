import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"


@dataclass(frozen=True)
class Settings:
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings(database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
