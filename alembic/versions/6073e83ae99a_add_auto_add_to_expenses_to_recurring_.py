"""Add auto_add_to_expenses to recurring_payments

Revision ID: 6073e83ae99a
Revises: 26a1e3fc3553
Create Date: 2025-12-29 12:45:54.062630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6073e83ae99a'
down_revision = '26a1e3fc3553'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('recurring_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auto_add_to_expenses', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('recurring_payments', schema=None) as batch_op:
        batch_op.drop_column('auto_add_to_expenses')