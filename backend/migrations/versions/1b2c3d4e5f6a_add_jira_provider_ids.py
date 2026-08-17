"""add Jira provider identifiers

Revision ID: 1b2c3d4e5f6a
Revises: 0a0b6c7d8e9f
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1b2c3d4e5f6a"
down_revision: str | Sequence[str] | None = "0a0b6c7d8e9f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("epics", sa.Column("provider_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_epics_provider_id", "epics", ["provider_id"])
    op.add_column("releases", sa.Column("provider_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_releases_provider_id", "releases", ["provider_id"])


def downgrade() -> None:
    op.drop_constraint("uq_releases_provider_id", "releases", type_="unique")
    op.drop_column("releases", "provider_id")
    op.drop_constraint("uq_epics_provider_id", "epics", type_="unique")
    op.drop_column("epics", "provider_id")
