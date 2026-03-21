"""add_slug_to_stores

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stores', sa.Column('slug', sa.String(), nullable=True))
    op.execute("""
        UPDATE stores
        SET slug = lower(
            regexp_replace(
                regexp_replace(name, '[^a-zA-Z0-9\\s-]', '', 'g'),
                '\\s+', '-', 'g'
            )
        )
    """)
    op.alter_column('stores', 'slug', nullable=False)
    op.create_index('ix_stores_slug', 'stores', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_stores_slug', table_name='stores')
    op.drop_column('stores', 'slug')
