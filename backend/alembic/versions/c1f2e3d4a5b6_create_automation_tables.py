"""create_automation_tables

Revision ID: c1f2e3d4a5b6
Revises: a342be1f7d6c
Create Date: 2026-07-19 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c1f2e3d4a5b6'
down_revision: Union[str, Sequence[str], None] = 'a342be1f7d6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create automation_rule table
    op.create_table(
        'automation_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('trigger', sa.String(length=50), nullable=False, server_default='on_transaction'),
        sa.Column('condition_logic', sa.String(length=10), nullable=False, server_default='AND'),
        sa.Column('conditions', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('actions', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automation_rule_id', 'automation_rule', ['id'], unique=False)
    op.create_index('ix_automation_rule_user_id', 'automation_rule', ['user_id'], unique=False)

    # 2. Create automation_execution table
    op.create_table(
        'automation_execution',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('trigger', sa.String(length=50), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('actions_executed', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('result_summary', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['automation_rule.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transaction.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automation_execution_id', 'automation_execution', ['id'], unique=False)
    op.create_index('ix_automation_execution_rule_id', 'automation_execution', ['rule_id'], unique=False)
    op.create_index('ix_automation_execution_user_id', 'automation_execution', ['user_id'], unique=False)
    op.create_index('ix_automation_execution_transaction_id', 'automation_execution', ['transaction_id'], unique=False)

    # 3. Add is_reviewed and is_archived to transaction table (SQLite batch mode)
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_reviewed', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('is_archived')
        batch_op.drop_column('is_reviewed')

    op.drop_index('ix_automation_execution_transaction_id', table_name='automation_execution')
    op.drop_index('ix_automation_execution_user_id', table_name='automation_execution')
    op.drop_index('ix_automation_execution_rule_id', table_name='automation_execution')
    op.drop_index('ix_automation_execution_id', table_name='automation_execution')
    op.drop_table('automation_execution')

    op.drop_index('ix_automation_rule_user_id', table_name='automation_rule')
    op.drop_index('ix_automation_rule_id', table_name='automation_rule')
    op.drop_table('automation_rule')
