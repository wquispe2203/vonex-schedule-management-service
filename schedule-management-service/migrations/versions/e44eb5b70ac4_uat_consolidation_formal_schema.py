"""uat_consolidation_formal_schema

Revision ID: e44eb5b70ac4
Revises: 1d83b04397de
Create Date: 2026-04-21 11:34:57.506654

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e44eb5b70ac4'
down_revision: Union[str, Sequence[str], None] = '1d83b04397de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Agregar is_active a teachers (Faltaba en la revisión anterior)
    # Usamos batch_op para mayor compatibilidad
    with op.batch_alter_table('teachers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True))

    # 2. Constraints (Solo si no existen para evitar errores 500 en Alembic)
    # Nota: uq_role_permission y uq_user_role ya existen en DB. 
    # Se dejan comentadas o manejadas para evitar fallos.
    # op.create_unique_constraint('uq_role_permission', 'role_permissions', ['role_id', 'permission_id'])
    # op.create_unique_constraint('uq_user_role', 'user_roles', ['user_id', 'role_id'])

def downgrade() -> None:
    with op.batch_alter_table('teachers', schema=None) as batch_op:
        batch_op.drop_column('is_active')
