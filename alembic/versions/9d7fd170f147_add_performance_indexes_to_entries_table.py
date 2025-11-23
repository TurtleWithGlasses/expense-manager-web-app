"""Add performance indexes to entries table

Revision ID: 9d7fd170f147
Revises: 91bdbf9e0309
Create Date: 2025-11-23 10:12:04.288043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d7fd170f147'
down_revision = '91bdbf9e0309'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes to entries table for better query performance
    # These indexes significantly improve filtering and sorting operations

    # Index on user_id - most critical as every query filters by user
    op.create_index('ix_entries_user_id', 'entries', ['user_id'])

    # Index on date - used for date range queries and sorting
    op.create_index('ix_entries_date', 'entries', ['date'])

    # Index on type - used for income/expense filtering
    op.create_index('ix_entries_type', 'entries', ['type'])

    # Index on category_id - used for category filtering
    op.create_index('ix_entries_category_id', 'entries', ['category_id'])

    # Composite index for common query pattern: user + date sorting
    op.create_index('ix_entries_user_date', 'entries', ['user_id', 'date'])


def downgrade() -> None:
    # Remove indexes in reverse order
    op.drop_index('ix_entries_user_date', table_name='entries')
    op.drop_index('ix_entries_category_id', table_name='entries')
    op.drop_index('ix_entries_type', table_name='entries')
    op.drop_index('ix_entries_date', table_name='entries')
    op.drop_index('ix_entries_user_id', table_name='entries')