"""add_location_fields_to_rpt

Revision ID: f97d68aaf2af
Revises: 749f2feb60cf
Create Date: 2026-04-28 11:19:13.914303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f97d68aaf2af'
down_revision: Union[str, Sequence[str], None] = '749f2feb60cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only add the columns we need, skipping redundant operations that might fail
    op.add_column('rpt_planilla', sa.Column('sede', sa.String(length=255), nullable=True))
    op.add_column('rpt_planilla', sa.Column('ciclo', sa.String(length=255), nullable=True))
    op.add_column('rpt_planilla', sa.Column('curso', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rpt_planilla', 'curso')
    op.drop_column('rpt_planilla', 'ciclo')
    op.drop_column('rpt_planilla', 'sede')
