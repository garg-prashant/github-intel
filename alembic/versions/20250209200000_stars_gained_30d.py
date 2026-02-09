"""Add stars_gained_30d to repositories for recent-trending sort.

Revision ID: 20250209200000
Revises: 20250209180000
Create Date: 2025-02-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250209200000"
down_revision: Union[str, None] = "20250209180000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("stars_gained_30d", sa.Integer(), nullable=True))
    op.create_index(
        "ix_repositories_stars_gained_30d",
        "repositories",
        ["stars_gained_30d"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_repositories_stars_gained_30d", table_name="repositories")
    op.drop_column("repositories", "stars_gained_30d")
