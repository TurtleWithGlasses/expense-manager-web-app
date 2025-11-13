"""fix_cascade_constraints_postgresql

Revision ID: 7dfb33c43cde
Revises: db983bf509da
Create Date: 2025-11-14 00:30:05.598528

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7dfb33c43cde'
down_revision = 'db983bf509da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Fix user_preferences foreign key constraint
        op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
        op.create_foreign_key(
            'user_preferences_user_id_fkey',
            'user_preferences', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )

        # Fix report_status foreign key constraint
        op.drop_constraint('report_status_user_id_fkey', 'report_status', type_='foreignkey')
        op.create_foreign_key(
            'report_status_user_id_fkey',
            'report_status', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Restore original user_preferences foreign key
        op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
        op.create_foreign_key(
            'user_preferences_user_id_fkey',
            'user_preferences', 'users',
            ['user_id'], ['id']
        )

        # Restore original report_status foreign key
        op.drop_constraint('report_status_user_id_fkey', 'report_status', type_='foreignkey')
        op.create_foreign_key(
            'report_status_user_id_fkey',
            'report_status', 'users',
            ['user_id'], ['id']
        )