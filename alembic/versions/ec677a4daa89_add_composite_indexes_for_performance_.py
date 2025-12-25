"""Add composite indexes for performance optimization

Revision ID: ec677a4daa89
Revises: 20250125_0002
Create Date: 2025-12-25 23:52:58.822629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec677a4daa89'
down_revision = '20250125_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite indexes for entries table - most frequently queried patterns

    # 1. User + Date + Type (used in forecasting, reports, dashboard)
    # Example query: WHERE user_id = X AND date >= Y AND date <= Z AND type = 'expense'
    op.create_index(
        'idx_entries_user_date_type',
        'entries',
        ['user_id', 'date', 'type'],
        unique=False
    )

    # 2. User + Type + Date DESC (used for sorted queries, recent entries)
    # Example query: WHERE user_id = X AND type = 'expense' ORDER BY date DESC
    op.create_index(
        'idx_entries_user_type_date_desc',
        'entries',
        ['user_id', 'type', sa.text('date DESC')],
        unique=False
    )

    # 3. User + Category + Date (used for category-specific analysis)
    # Example query: WHERE user_id = X AND category_id = Y AND date >= Z
    op.create_index(
        'idx_entries_user_category_date',
        'entries',
        ['user_id', 'category_id', 'date'],
        unique=False
    )

    # 4. User + Date (for total spending queries without type filter)
    # Example query: WHERE user_id = X AND date >= Y AND date <= Z
    op.create_index(
        'idx_entries_user_date',
        'entries',
        ['user_id', 'date'],
        unique=False
    )

    # Composite indexes for recurring_payments table

    # 1. User + Active + Start Date (for finding active recurring payments)
    op.create_index(
        'idx_recurring_payments_user_active_start',
        'recurring_payments',
        ['user_id', 'is_active', 'start_date'],
        unique=False
    )

    # Composite indexes for forecasts table (if caching is used)

    # 1. User + Type + Created (for finding cached forecasts)
    op.create_index(
        'idx_forecasts_user_type_created',
        'forecasts',
        ['user_id', 'forecast_type', sa.text('created_at DESC')],
        unique=False
    )

    # Composite indexes for scenarios table

    # 1. User + Active + Created (for listing active scenarios)
    op.create_index(
        'idx_scenarios_user_active_created',
        'scenarios',
        ['user_id', 'is_active', sa.text('created_at DESC')],
        unique=False
    )


def downgrade() -> None:
    # Drop composite indexes in reverse order
    op.drop_index('idx_scenarios_user_active_created', table_name='scenarios')
    op.drop_index('idx_forecasts_user_type_created', table_name='forecasts')
    op.drop_index('idx_recurring_payments_user_active_start', table_name='recurring_payments')
    op.drop_index('idx_entries_user_date', table_name='entries')
    op.drop_index('idx_entries_user_category_date', table_name='entries')
    op.drop_index('idx_entries_user_type_date_desc', table_name='entries')
    op.drop_index('idx_entries_user_date_type', table_name='entries')