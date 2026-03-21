"""add_store_id_to_market_offers

Revision ID: e27028b78fab
Revises: 5e3dc97c03b0
Create Date: 2026-03-20 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e27028b78fab'
down_revision: Union[str, Sequence[str], None] = '5e3dc97c03b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add nullable store_id column
    op.add_column('market_offers', sa.Column('store_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_market_offers_store_id', 'market_offers', 'stores', ['store_id'], ['id'])
    
    # Step 2: Data migration mapping store_name to store_id
    store_names = [
        "Brazil Pickleball Store",
        "PCKL House",
        "Drop Shot Brasil",
        "ProPadel",
        "ProSpin",
        "Joola Brasil",
        "yoSports",
        "Loja Supremo",
        "Shark",
    ]
    for name in store_names:
        op.execute(
            f"UPDATE market_offers SET store_id = "
            f"(SELECT id FROM stores WHERE name = '{name}') "
            f"WHERE store_name = '{name}'"
        )
    
    # Step 3: Enforce NOT NULL after all rows are mapped
    op.alter_column('market_offers', 'store_id', nullable=False)
    
    # Step 4: Drop the now-redundant store_name column
    op.drop_column('market_offers', 'store_name')


def downgrade() -> None:
    op.add_column('market_offers', sa.Column('store_name', sa.String(), nullable=True))
    op.execute(
        "UPDATE market_offers SET store_name = "
        "(SELECT name FROM stores WHERE stores.id = market_offers.store_id)"
    )
    op.alter_column('market_offers', 'store_name', nullable=False)
    op.drop_constraint('fk_market_offers_store_id', 'market_offers', type_='foreignkey')
    op.drop_column('market_offers', 'store_id')
