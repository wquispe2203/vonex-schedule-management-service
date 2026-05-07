"""add_observability_to_xml_uploads

Revision ID: 992c6ae1636a
Revises: 1417036a2c1c
Create Date: 2026-04-28 11:29:28.914303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '992c6ae1636a'
down_revision: Union[str, Sequence[str], None] = '1417036a2c1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('xml_uploads', sa.Column('fallback_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('xml_uploads', sa.Column('process_time_ms', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('xml_uploads', 'process_time_ms')
    op.drop_column('xml_uploads', 'fallback_count')
