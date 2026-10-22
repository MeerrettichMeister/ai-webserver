import os
from dataclasses import dataclass
from functools import lru_cache

# 127.0.0.1, not localhost: on Windows localhost tries ::1 first, where Docker's port forward
# accepts the connection but never answers, so connecting hangs.
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres"


@dataclass(frozen=True)
class Settings:
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings(database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
