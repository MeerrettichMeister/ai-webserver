"""plain text steps and numeric amounts

Revision ID: 0b146d5f06df
Revises: 01b7f116263a
Create Date: 2026-10-22 15:05:33.114626

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b146d5f06df"
down_revision: str | Sequence[str] | None = "01b7f116263a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Steps first: their composite FK depends on uq_ingredient_recipe_id_id.
    op.drop_index(op.f("ix_step_ingredient_id"), table_name="step")
    op.drop_constraint(
        op.f("fk_step_recipe_id_ingredient_id_ingredient"), "step", type_="foreignkey"
    )
    op.drop_column("step", "ingredient_id")
    op.drop_constraint(op.f("uq_ingredient_recipe_id_id"), "ingredient", type_="unique")
    # Fails if an existing amount is not a number.
    op.alter_column(
        "ingredient",
        "amount",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.Numeric(precision=10, scale=3),
        existing_nullable=False,
        postgresql_using="amount::numeric(10, 3)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "ingredient",
        "amount",
        existing_type=sa.Numeric(precision=10, scale=3),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
        postgresql_using="amount::varchar(50)",
    )
    op.create_unique_constraint(
        op.f("uq_ingredient_recipe_id_id"), "ingredient", ["recipe_id", "id"]
    )
    # Which ingredient a step used is gone, so this fails if there are any steps.
    op.add_column("step", sa.Column("ingredient_id", sa.UUID(), nullable=False))
    op.create_foreign_key(
        op.f("fk_step_recipe_id_ingredient_id_ingredient"),
        "step",
        "ingredient",
        ["recipe_id", "ingredient_id"],
        ["recipe_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_step_ingredient_id"), "step", ["ingredient_id"], unique=False)
