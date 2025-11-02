"""Add theme column to user_preferences

Revision ID: 20251025_0001
Revises:
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251025_0001'
down_revision = None  # Update this to the latest migration ID in your system
branch_labels = None
depends_on = None


def upgrade():
    # Add theme column to user_preferences table
    # Using batch mode for SQLite compatibility
    with op.batch_alter_table('user_preferences') as batch_op:
        batch_op.add_column(
            sa.Column('theme', sa.String(length=10), nullable=True, server_default='dark')
        )

    # Update existing rows to have 'dark' theme
    op.execute("UPDATE user_preferences SET theme = 'dark' WHERE theme IS NULL")

    # Make the column non-nullable after setting default values
    with op.batch_alter_table('user_preferences') as batch_op:
        batch_op.alter_column('theme', nullable=False)


def downgrade():
    # Remove theme column from user_preferences table
    with op.batch_alter_table('user_preferences') as batch_op:
        batch_op.drop_column('theme')
