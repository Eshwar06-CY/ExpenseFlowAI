"""create_import_tables

Revision ID: 99037c27cbfe
Revises: b51e7f158ffa
Create Date: 2026-07-19 09:52:44.644152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99037c27cbfe'
down_revision: Union[str, Sequence[str], None] = 'b51e7f158ffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('import_history',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('rows_imported', sa.Integer(), nullable=False),
    sa.Column('rows_skipped', sa.Integer(), nullable=False),
    sa.Column('rows_failed', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_history_id'), 'import_history', ['id'], unique=False)
    op.create_index(op.f('ix_import_history_user_id'), 'import_history', ['user_id'], unique=False)
    op.create_table('import_template',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('date_col', sa.String(length=100), nullable=True),
    sa.Column('amount_col', sa.String(length=100), nullable=True),
    sa.Column('desc_col', sa.String(length=100), nullable=True),
    sa.Column('cat_col', sa.String(length=100), nullable=True),
    sa.Column('acc_col', sa.String(length=100), nullable=True),
    sa.Column('ref_col', sa.String(length=100), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_template_id'), 'import_template', ['id'], unique=False)
    op.create_index(op.f('ix_import_template_user_id'), 'import_template', ['user_id'], unique=False)

    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('import_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_transaction_import_id'), ['import_id'], unique=False)
        batch_op.create_foreign_key('fk_transaction_import_history', 'import_history', ['import_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transaction_import_history', type_='foreignkey')
        batch_op.drop_index(op.f('ix_transaction_import_id'))
        batch_op.drop_column('import_id')

    op.drop_index(op.f('ix_import_template_user_id'), table_name='import_template')
    op.drop_index(op.f('ix_import_template_id'), table_name='import_template')
    op.drop_table('import_template')
    
    op.drop_index(op.f('ix_import_history_user_id'), table_name='import_history')
    op.drop_index(op.f('ix_import_history_id'), table_name='import_history')
    op.drop_table('import_history')
