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
    # SQLite uses batch mode to recreate table with CASCADE constraint
    # PostgreSQL will drop and recreate the foreign key with CASCADE
    with op.batch_alter_table('report_status', schema=None, recreate='always') as batch_op:
        pass  # The recreation will pick up the ondelete='CASCADE' from the model


def downgrade() -> None:
    # Downgrade by recreating without CASCADE
    with op.batch_alter_table('report_status', schema=None, recreate='always') as batch_op:
        pass  # The recreation will pick up the original constraint