"""add audit log columns

Revision ID: 52994833c2a3
Revises: 145c3a5db8dc
Create Date: 2026-06-14 14:30:44.322055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52994833c2a3'
down_revision: Union[str, Sequence[str], None] = '145c3a5db8dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_logs', sa.Column('action', sa.String(length=50), nullable=True))
    op.add_column('audit_logs', sa.Column('entity_type', sa.String(length=50), nullable=True))
    op.add_column('audit_logs', sa.Column('entity_id', sa.Integer(), nullable=True))
    op.add_column('audit_logs', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('audit_logs', sa.Column('user_agent', sa.String(length=255), nullable=True))
    op.add_column('audit_logs', sa.Column('actor_name', sa.String(length=100), nullable=True))
    op.add_column('audit_logs', sa.Column('description', sa.String(length=500), nullable=True))
    op.alter_column('audit_logs', 'field',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_audit_logs_ip_address', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.alter_column('audit_logs', 'field',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.drop_column('audit_logs', 'description')
    op.drop_column('audit_logs', 'actor_name')
    op.drop_column('audit_logs', 'user_agent')
    op.drop_column('audit_logs', 'ip_address')
    op.drop_column('audit_logs', 'entity_id')
    op.drop_column('audit_logs', 'entity_type')
    op.drop_column('audit_logs', 'action')
