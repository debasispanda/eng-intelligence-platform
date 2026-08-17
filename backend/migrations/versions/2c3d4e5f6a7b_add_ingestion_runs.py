"""add ingestion run tracking

Revision ID: 2c3d4e5f6a7b
Revises: 1b2c3d4e5f6a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2c3d4e5f6a7b"
down_revision: str | Sequence[str] | None = "1b2c3d4e5f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_synchronized", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_runs_organization_provider_started_at",
        "ingestion_runs",
        ["organization_id", "provider", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_organization_provider_started_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
