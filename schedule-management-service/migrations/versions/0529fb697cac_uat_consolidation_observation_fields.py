"""uat_consolidation_observation_fields

Revision ID: 0529fb697cac
Revises: e1c5dfc3388a
Create Date: 2026-04-21 11:50:12.586114

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0529fb697cac'
down_revision: Union[str, Sequence[str], None] = 'e1c5dfc3388a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Ignoramos constraints duplicados
    # op.create_unique_constraint('uq_role_permission', 'role_permissions', ['role_id', 'permission_id'])
    # op.create_unique_constraint('uq_user_role', 'user_roles', ['user_id', 'role_id'])
    
    op.add_column('observations', sa.Column('discount_type', sa.String(length=50), nullable=True, server_default='SIMPLE'))
    op.add_column('observations', sa.Column('teacher_uid', sa.UUID(), nullable=True))
    op.add_column('observations', sa.Column('replacement_teacher_uid', sa.UUID(), nullable=True))
    op.add_column('observations', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('observations', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

def downgrade() -> None:
    op.drop_column('observations', 'created_at')
    op.drop_column('observations', 'description')
    op.drop_column('observations', 'replacement_teacher_uid')
    op.drop_column('observations', 'teacher_uid')
    op.drop_column('observations', 'discount_type')
