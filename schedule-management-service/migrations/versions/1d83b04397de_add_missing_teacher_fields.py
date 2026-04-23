"""add missing teacher fields

Revision ID: 1d83b04397de
Revises: 18d9f168a2eb
Create Date: 2026-04-21 10:40:27.796123

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1d83b04397de'
down_revision: Union[str, Sequence[str], None] = '18d9f168a2eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('teachers', sa.Column('short_name', sa.String(length=50), nullable=True))
    op.add_column('teachers', sa.Column('razon_social', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('teachers', 'razon_social')
    op.drop_column('teachers', 'short_name')
