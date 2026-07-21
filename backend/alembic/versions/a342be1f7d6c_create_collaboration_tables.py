"""create_collaboration_tables

Revision ID: a342be1f7d6c
Revises: 38474c4b877e
Create Date: 2026-07-19 10:14:58.510639

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a342be1f7d6c'
down_revision: Union[str, Sequence[str], None] = '38474c4b877e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Workspace & Audit Tables
    op.create_table('workspace',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_id'), 'workspace', ['id'], unique=False)
    
    op.create_table('audit_log',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_id'), 'audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_log_workspace_id'), 'audit_log', ['workspace_id'], unique=False)
    
    op.create_table('comment',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_entity_id'), 'comment', ['entity_id'], unique=False)
    op.create_index(op.f('ix_comment_id'), 'comment', ['id'], unique=False)
    op.create_index(op.f('ix_comment_user_id'), 'comment', ['user_id'], unique=False)
    op.create_index(op.f('ix_comment_workspace_id'), 'comment', ['workspace_id'], unique=False)
    
    op.create_table('workspace_member',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('invited_by_id', sa.Integer(), nullable=True),
        sa.Column('is_accepted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['invited_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_member_id'), 'workspace_member', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_member_user_id'), 'workspace_member', ['user_id'], unique=False)
    op.create_index(op.f('ix_workspace_member_workspace_id'), 'workspace_member', ['workspace_id'], unique=False)

    # 2. Add workspace_id columns in Batch mode to support SQLite constraints modifications
    tables_to_migrate = [
        'account', 'bill', 'budget', 'daily_briefing', 'financial_event',
        'financial_insight', 'goal', 'import_history', 'import_template',
        'recurring_transaction', 'scenario', 'transaction'
    ]

    for table in tables_to_migrate:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f(f'ix_{table}_workspace_id'), ['workspace_id'], unique=False)
            batch_op.create_foreign_key(f'fk_{table}_workspace_id', 'workspace', ['workspace_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    tables_to_migrate = [
        'account', 'bill', 'budget', 'daily_briefing', 'financial_event',
        'financial_insight', 'goal', 'import_history', 'import_template',
        'recurring_transaction', 'scenario', 'transaction'
    ]

    for table in tables_to_migrate:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_workspace_id', type_='foreignkey')
            batch_op.drop_index(batch_op.f(f'ix_{table}_workspace_id'))
            batch_op.drop_column('workspace_id')

    op.drop_index(op.f('ix_workspace_member_workspace_id'), table_name='workspace_member')
    op.drop_index(op.f('ix_workspace_member_user_id'), table_name='workspace_member')
    op.drop_index(op.f('ix_workspace_member_id'), table_name='workspace_member')
    op.drop_table('workspace_member')
    
    op.drop_index(op.f('ix_comment_workspace_id'), table_name='comment')
    op.drop_index(op.f('ix_comment_user_id'), table_name='comment')
    op.drop_index(op.f('ix_comment_id'), table_name='comment')
    op.drop_index(op.f('ix_comment_entity_id'), table_name='comment')
    op.drop_table('comment')
    
    op.drop_index(op.f('ix_audit_log_workspace_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_user_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_id'), table_name='audit_log')
    op.drop_table('audit_log')
    
    op.drop_index(op.f('ix_workspace_id'), table_name='workspace')
    op.drop_table('workspace')
