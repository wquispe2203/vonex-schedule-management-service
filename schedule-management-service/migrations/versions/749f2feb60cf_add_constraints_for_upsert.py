"""add_constraints_for_upsert

Revision ID: 749f2feb60cf
Revises: 328f6913f9d0
Create Date: 2026-04-24 17:10:45.393452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '749f2feb60cf'
down_revision: Union[str, Sequence[str], None] = '328f6913f9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. RptPlanilla: Add hora_inicio and UniqueConstraint
    op.add_column('rpt_planilla', sa.Column('hora_inicio', sa.Time(), nullable=True))
    op.create_unique_constraint('uq_rpt_planilla_unique', 'rpt_planilla', ['fecha_clase', 'docente', 'hora_inicio'])
    
    # 2. ScheduleSession: Add UniqueConstraint
    op.create_unique_constraint('uq_session_lesson_time', 'schedule_sessions', ['lesson_id', 'session_date', 'start_time'])


def downgrade() -> None:
    op.drop_constraint('uq_session_lesson_time', 'schedule_sessions', type_='unique')
    op.drop_constraint('uq_rpt_planilla_unique', 'rpt_planilla', type_='unique')
    op.drop_column('rpt_planilla', 'hora_inicio')
