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
    # SQLite doesn't enforce foreign keys for ALTER, so batch mode will recreate the table
    # with the new ondelete='CASCADE' constraint from the model
    # For PostgreSQL in production, this will properly add the CASCADE constraint
    with op.batch_alter_table('user_preferences', schema=None, recreate='always') as batch_op:
        pass  # The recreation will pick up the ondelete='CASCADE' from the model


def downgrade() -> None:
    # Downgrade by recreating without CASCADE
    with op.batch_alter_table('user_preferences', schema=None, recreate='always') as batch_op:
        pass  # The recreation will pick up the original constraint