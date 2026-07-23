"""create_notification_preferences_and_extended_fields

Revision ID: f99b28cf9158
Revises: deb43d1f520c
Create Date: 2026-07-23 11:57:26.685622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f99b28cf9158'
down_revision: Union[str, Sequence[str], None] = 'deb43d1f520c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'notification_preference' not in tables:
        op.create_table(
            'notification_preference',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('enable_budget_alerts', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_bill_reminders', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_goal_updates', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_forecast_warnings', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_ai_recommendations', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_security_alerts', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_achievements', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_email_notifications', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('enable_in_app', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('digest_frequency', sa.String(length=20), server_default='weekly', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notification_preference_id'), 'notification_preference', ['id'], unique=False)
        op.create_index(op.f('ix_notification_preference_user_id'), 'notification_preference', ['user_id'], unique=True)

    columns = [c['name'] for c in inspector.get_columns('notification')]

    with op.batch_alter_table('notification') as batch_op:
        if 'category' not in columns:
            batch_op.add_column(sa.Column('category', sa.String(length=50), server_default='system', nullable=False))
            batch_op.create_index(op.f('ix_notification_category'), ['category'], unique=False)
        if 'priority' not in columns:
            batch_op.add_column(sa.Column('priority', sa.String(length=20), server_default='medium', nullable=False))
            batch_op.create_index(op.f('ix_notification_priority'), ['priority'], unique=False)
        if 'icon' not in columns:
            batch_op.add_column(sa.Column('icon', sa.String(length=50), nullable=True))
        if 'action_url' not in columns:
            batch_op.add_column(sa.Column('action_url', sa.String(length=255), nullable=True))
        if 'metadata_json' not in columns:
            batch_op.add_column(sa.Column('metadata_json', sa.Text(), nullable=True))
        if 'expires_at' not in columns:
            batch_op.add_column(sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
        if 'updated_at' not in columns:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        
        batch_op.alter_column('message', existing_type=sa.VARCHAR(length=255), type_=sa.String(length=500), existing_nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('notification') as batch_op:
        batch_op.drop_index(op.f('ix_notification_priority'))
        batch_op.drop_index(op.f('ix_notification_category'))
        batch_op.alter_column('message', existing_type=sa.String(length=500), type_=sa.VARCHAR(length=255), existing_nullable=False)
        batch_op.drop_column('updated_at')
        batch_op.drop_column('expires_at')
        batch_op.drop_column('metadata_json')
        batch_op.drop_column('action_url')
        batch_op.drop_column('icon')
        batch_op.drop_column('priority')
        batch_op.drop_column('category')

    op.drop_index(op.f('ix_notification_preference_user_id'), table_name='notification_preference')
    op.drop_index(op.f('ix_notification_preference_id'), table_name='notification_preference')
    op.drop_table('notification_preference')
