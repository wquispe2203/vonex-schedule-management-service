"""uat_consolidation_xml_fields

Revision ID: e1c5dfc3388a
Revises: e44eb5b70ac4
Create Date: 2026-04-21 11:41:26.150273

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1c5dfc3388a'
down_revision: Union[str, Sequence[str], None] = 'e44eb5b70ac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Ignoramos constraints duplicados que ya existen en DB
    # op.create_unique_constraint('uq_role_permission', 'role_permissions', ['role_id', 'permission_id'])
    # op.create_unique_constraint('uq_user_role', 'user_roles', ['user_id', 'role_id'])
    
    op.add_column('xml_uploads', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('xml_uploads', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('xml_uploads', sa.Column('is_force_overwrite', sa.Boolean(), server_default='false', nullable=True))

def downgrade() -> None:
    op.drop_column('xml_uploads', 'is_force_overwrite')
    op.drop_column('xml_uploads', 'end_date')
    op.drop_column('xml_uploads', 'start_date')
