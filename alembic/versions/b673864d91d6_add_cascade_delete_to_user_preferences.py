"""add_cascade_delete_to_user_preferences

Revision ID: b673864d91d6
Revises: af4ec7fe5872
Create Date: 2025-11-13 23:53:02.498158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b673864d91d6'
down_revision = 'af4ec7fe5872'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if we're using PostgreSQL or SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Drop and recreate the foreign key with CASCADE
        op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
        op.create_foreign_key(
            'user_preferences_user_id_fkey',
            'user_preferences', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
    else:
        # SQLite: Use batch mode to recreate table
        with op.batch_alter_table('user_preferences', schema=None, recreate='always') as batch_op:
            pass  # The recreation will pick up the ondelete='CASCADE' from the model


def downgrade() -> None:
    # Check if we're using PostgreSQL or SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # PostgreSQL: Drop CASCADE and restore original foreign key
        op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
        op.create_foreign_key(
            'user_preferences_user_id_fkey',
            'user_preferences', 'users',
            ['user_id'], ['id']
        )
    else:
        # SQLite: Use batch mode to recreate table
        with op.batch_alter_table('user_preferences', schema=None, recreate='always') as batch_op:
            pass  # The recreation will pick up the original constraint