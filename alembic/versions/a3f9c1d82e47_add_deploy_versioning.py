"""add deploy versioning

Revision ID: a3f9c1d82e47
Revises: d081a2cccc0e
Create Date: 2026-03-20 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3f9c1d82e47'
down_revision: Union[str, Sequence[str], None] = 'd081a2cccc0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — add version_id columns, staging table, and deploy_logs table."""

    # 1. Add version_id to market_offers
    op.add_column(
        "market_offers",
        sa.Column("version_id", sa.Integer(), nullable=True),
    )

    # 2. Add version_id to paddle_master
    op.add_column(
        "paddle_master",
        sa.Column("version_id", sa.Integer(), nullable=True),
    )

    # 3. Create market_offers_staging table (batch isolation before publish)
    op.create_table(
        "market_offers_staging",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("paddle_id", postgresql.UUID(), nullable=False),
        sa.Column("store_name", sa.String(), nullable=False),
        sa.Column("price_brl", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_offers_staging_batch_id", "market_offers_staging", ["batch_id"], unique=False)

    # 4. Create deploy_logs table
    op.create_table(
        "deploy_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("scrapers_passed", sa.Integer(), nullable=False),
        sa.Column("scrapers_total", sa.Integer(), nullable=False, server_default="11"),
        sa.Column("products_published", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forced", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("operator_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deploy_logs_batch_id", "deploy_logs", ["batch_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema — remove deploy versioning additions."""

    # Reverse order
    op.drop_index("ix_deploy_logs_batch_id", table_name="deploy_logs")
    op.drop_table("deploy_logs")

    op.drop_index("ix_market_offers_staging_batch_id", table_name="market_offers_staging")
    op.drop_table("market_offers_staging")

    op.drop_column("paddle_master", "version_id")
    op.drop_column("market_offers", "version_id")
