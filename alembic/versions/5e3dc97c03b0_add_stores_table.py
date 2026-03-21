"""add_stores_table

Revision ID: 5e3dc97c03b0
Revises: e68bd0ed63d5
Create Date: 2026-03-20 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '5e3dc97c03b0'
down_revision: Union[str, Sequence[str], None] = 'e68bd0ed63d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), autoincrement=False, nullable=False),
        sa.Column('base_url', sa.String(), autoincrement=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', autoincrement=False, nullable=False),
        sa.Column('available_brands', postgresql.ARRAY(sa.String()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='stores_pkey')
    )
    
    op.bulk_insert(
        op.get_bind(),
        'stores',
        [
            {'name': 'Brazil Pickleball Store', 'base_url': 'www.brazilpickleballstore.com.br', 'is_active': True, 'available_brands': ['Selkirk', 'JOOLA', 'Diadem', 'Gearbox']},
            {'name': 'Joola Brasil', 'base_url': 'joola.com.br', 'is_active': True, 'available_brands': ['JOOLA']},
            {'name': 'yoSports', 'base_url': 'yosports.com.br', 'is_active': True, 'available_brands': ['Selkirk', 'JOOLA', 'Head', 'Wilson']},
            {'name': 'Loja Supremo', 'base_url': 'www.lojasupremo.com.br', 'is_active': True, 'available_brands': ['Selkirk', 'JOOLA', 'Adidas']},
            {'name': 'Shark', 'base_url': 'sharkbeachtennis.com.br', 'is_active': True, 'available_brands': ['Shark']},
            {'name': 'ProSpin', 'base_url': 'www.prospin.com.br', 'is_active': True, 'available_brands': ['JOOLA', 'Selkirk', 'Drop Shot']},
            {'name': 'Drop Shot Brasil', 'base_url': 'www.dropshot.com.br', 'is_active': True, 'available_brands': ['Drop Shot']},
            {'name': 'PCKL House', 'base_url': 'www.pcklhouse.com.br', 'is_active': True, 'available_brands': ['PCKL', 'Selkirk']},
            {'name': 'ProPadel', 'base_url': 'www.lojapropadel.com.br', 'is_active': True, 'available_brands': ['JOOLA', 'Selkirk', 'Head']},
            {'name': 'Just Paddles', 'base_url': 'www.justpaddles.com', 'is_active': True, 'available_brands': ['Selkirk', 'JOOLA', 'Paddletek', 'Engage']},
        ]
    )


def downgrade() -> None:
    op.drop_table('stores')
