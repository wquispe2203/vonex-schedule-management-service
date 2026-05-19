"""create_teacher_name_overrides

Revision ID: 81848d0af784
Revises: 992c6ae1636a
Create Date: 2026-05-18 12:23:10.670584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81848d0af784'
down_revision: Union[str, Sequence[str], None] = '992c6ae1636a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('teacher_name_overrides',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('xml_name_raw', sa.String(length=255), nullable=False),
    sa.Column('xml_name_normalized', sa.String(length=400), nullable=False),
    sa.Column('teacher_id', sa.UUID(), nullable=False),
    sa.Column('xml_upload_id', sa.UUID(), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['xml_upload_id'], ['xml_uploads.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('teacher_name_overrides')

