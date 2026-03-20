"""add quality_metrics table

Revision ID: add_quality_metrics
Revises: a3f9c1d82e47
Create Date: 2026-03-20 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_quality_metrics'
down_revision: Union[str, Sequence[str], None] = 'a3f9c1d82e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('quality_metrics',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('scraper_name', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('run_id', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('freshness_hours', sa.DOUBLE_PRECISION(), autoincrement=False, nullable=False),
        sa.Column('completeness_pct', sa.DOUBLE_PRECISION(), autoincrement=False, nullable=False),
        sa.Column('coverage_pct', sa.DOUBLE_PRECISION(), autoincrement=False, nullable=False),
        sa.Column('product_count', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('error_rate', sa.DOUBLE_PRECISION(), autoincrement=False, nullable=False),
        sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('checked_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='quality_metrics_pkey')
    )
    op.create_index('ix_quality_metrics_scraper_name', 'quality_metrics', ['scraper_name'], unique=False)
    op.create_index('ix_quality_metrics_run_id', 'quality_metrics', ['run_id'], unique=False)
    op.create_index('ix_quality_metrics_scraper_checked', 'quality_metrics', ['scraper_name', 'checked_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_quality_metrics_scraper_checked', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_run_id', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_scraper_name', table_name='quality_metrics')
    op.drop_table('quality_metrics')
