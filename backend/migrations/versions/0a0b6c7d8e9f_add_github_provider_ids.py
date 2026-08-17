"""add GitHub provider identifiers

Revision ID: 0a0b6c7d8e9f
Revises: 5c1fccfd9efb
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0a0b6c7d8e9f"
down_revision: str | Sequence[str] | None = "5c1fccfd9efb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pull_requests", sa.Column("provider_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_pull_requests_provider_id", "pull_requests", ["provider_id"])
    op.add_column("builds", sa.Column("provider_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_builds_provider_id", "builds", ["provider_id"])


def downgrade() -> None:
    op.drop_constraint("uq_builds_provider_id", "builds", type_="unique")
    op.drop_column("builds", "provider_id")
    op.drop_constraint("uq_pull_requests_provider_id", "pull_requests", type_="unique")
    op.drop_column("pull_requests", "provider_id")
