"""add_idempotency_to_xml_upload

Revision ID: 328f6913f9d0
Revises: cdfde098f7a4
Create Date: 2026-04-24 17:09:01.700486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '328f6913f9d0'
down_revision: Union[str, Sequence[str], None] = 'cdfde098f7a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to xml_uploads
    op.add_column('xml_uploads', sa.Column('file_hash', sa.String(length=64), nullable=True))
    op.add_column('xml_uploads', sa.Column('status', sa.String(length=20), server_default='PENDING'))
    op.add_column('xml_uploads', sa.Column('total_records', sa.Integer(), server_default='0'))
    op.add_column('xml_uploads', sa.Column('processed_records', sa.Integer(), server_default='0'))
    op.add_column('xml_uploads', sa.Column('error_summary', sa.Text(), nullable=True))
    
    # Create index for file_hash
    op.create_index(op.f('ix_xml_uploads_file_hash'), 'xml_uploads', ['file_hash'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_xml_uploads_file_hash'), table_name='xml_uploads')
    op.drop_column('xml_uploads', 'error_summary')
    op.drop_column('xml_uploads', 'processed_records')
    op.drop_column('xml_uploads', 'total_records')
    op.drop_column('xml_uploads', 'status')
    op.drop_column('xml_uploads', 'file_hash')
