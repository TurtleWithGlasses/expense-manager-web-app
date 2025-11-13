"""add_cascade_delete_to_report_status

Revision ID: db983bf509da
Revises: b673864d91d6
Create Date: 2025-11-13 23:58:43.556518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db983bf509da'
down_revision = 'b673864d91d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if we're using PostgreSQL or SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Drop and recreate the foreign key with CASCADE
        op.drop_constraint('report_status_user_id_fkey', 'report_status', type_='foreignkey')
        op.create_foreign_key(
            'report_status_user_id_fkey',
            'report_status', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
    else:
        # SQLite: Use batch mode to recreate table
        with op.batch_alter_table('report_status', schema=None, recreate='always') as batch_op:
            pass  # The recreation will pick up the ondelete='CASCADE' from the model


def downgrade() -> None:
    # Check if we're using PostgreSQL or SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Drop CASCADE and restore original foreign key
        op.drop_constraint('report_status_user_id_fkey', 'report_status', type_='foreignkey')
        op.create_foreign_key(
            'report_status_user_id_fkey',
            'report_status', 'users',
            ['user_id'], ['id']
        )
    else:
        # SQLite: Use batch mode to recreate table
        with op.batch_alter_table('report_status', schema=None, recreate='always') as batch_op:
            pass  # The recreation will pick up the original constraint