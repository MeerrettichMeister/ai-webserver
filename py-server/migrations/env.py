import logging

from alembic import context
from sqlalchemy import create_engine, pool

from py_server.config import get_settings
from py_server.model import Base

# There is no alembic.ini; log alembic's progress (e.g. "Running upgrade ...") to stderr.
logging.basicConfig(format="%(levelname)-5.5s [%(name)s] %(message)s", level=logging.WARNING)
logging.getLogger("alembic").setLevel(logging.INFO)

target_metadata = Base.metadata
database_url = get_settings().database_url


def run_migrations_offline() -> None:
    """Emit the migration SQL to stdout instead of running it (`alembic upgrade --sql`)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
