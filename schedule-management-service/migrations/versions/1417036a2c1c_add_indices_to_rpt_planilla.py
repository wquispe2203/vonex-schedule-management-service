"""add_indices_to_rpt_planilla

Revision ID: 1417036a2c1c
Revises: f97d68aaf2af
Create Date: 2026-04-28 11:24:45.078427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1417036a2c1c'
down_revision: Union[str, Sequence[str], None] = 'f97d68aaf2af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Sede is heavily used for filtering
    op.create_index(op.f('ix_rpt_planilla_sede'), 'rpt_planilla', ['sede'], unique=False)
    # Ciclo is used for filtering as 'aula'
    op.create_index(op.f('ix_rpt_planilla_ciclo'), 'rpt_planilla', ['ciclo'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_rpt_planilla_ciclo'), table_name='rpt_planilla')
    op.drop_index(op.f('ix_rpt_planilla_sede'), table_name='rpt_planilla')
