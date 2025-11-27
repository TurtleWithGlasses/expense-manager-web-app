"""fix production migration by applying all pending changes safely

Revision ID: fix_production
Revises: 7dfb33c43cde
Create Date: 2025-11-27 17:55:00.000000

This migration applies all changes from the branching migrations
in a safe way, checking for existing columns before creating them.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_production'
down_revision = '7dfb33c43cde'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # From 91bdbf9e0309: Add AI fields to entries (if not exists)
    if not column_exists('entries', 'ai_suggested_category_id'):
        op.add_column('entries', sa.Column('ai_suggested_category_id', sa.Integer(), nullable=True))
    if not column_exists('entries', 'ai_confidence_score'):
        op.add_column('entries', sa.Column('ai_confidence_score', sa.Numeric(precision=3, scale=2), nullable=True))
    if not column_exists('entries', 'merchant_name'):
        op.add_column('entries', sa.Column('merchant_name', sa.String(length=255), nullable=True))
    if not column_exists('entries', 'location_data'):
        op.add_column('entries', sa.Column('location_data', sa.String(), nullable=True))
    if not column_exists('entries', 'ai_processed'):
        op.add_column('entries', sa.Column('ai_processed', sa.Boolean(), nullable=False, server_default='0'))

    # From 9d7fd170f147: Add performance indexes to entries table
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('entries')]

    if 'idx_entries_user_date' not in existing_indexes:
        op.create_index('idx_entries_user_date', 'entries', ['user_id', 'date'], unique=False)
    if 'idx_entries_category' not in existing_indexes:
        op.create_index('idx_entries_category', 'entries', ['category_id'], unique=False)
    if 'idx_entries_date_range' not in existing_indexes:
        op.create_index('idx_entries_date_range', 'entries', ['date'], unique=False)

    # From ae483fa17f81: Add recurring payments and reminders
    if not table_exists('recurring_payments'):
        op.create_table('recurring_payments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('frequency', sa.String(length=20), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('last_processed_date', sa.Date(), nullable=True),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('reminder_enabled', sa.Boolean(), nullable=False),
            sa.Column('reminder_days_before', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_recurring_payments_user', 'recurring_payments', ['user_id'], unique=False)
        op.create_index('idx_recurring_payments_next_date', 'recurring_payments', ['start_date'], unique=False)

    # From f3c5d1a8e9b2: Add payment history and auto-linking
    if not table_exists('payment_history'):
        op.create_table('payment_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('recurring_payment_id', sa.Integer(), nullable=False),
            sa.Column('entry_id', sa.Integer(), nullable=True),
            sa.Column('expected_date', sa.Date(), nullable=False),
            sa.Column('actual_date', sa.Date(), nullable=True),
            sa.Column('expected_amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('actual_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('auto_linked', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['entry_id'], ['entries.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_payment_history_recurring', 'payment_history', ['recurring_payment_id'], unique=False)
        op.create_index('idx_payment_history_entry', 'payment_history', ['entry_id'], unique=False)
        op.create_index('idx_payment_history_status', 'payment_history', ['status'], unique=False)

    if not column_exists('entries', 'payment_history_id'):
        op.add_column('entries', sa.Column('payment_history_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_entries_payment_history', 'entries', 'payment_history', ['payment_history_id'], ['id'], ondelete='SET NULL')

    # From ce6391aadad7: Add historical reports table
    if not table_exists('historical_reports'):
        op.create_table('historical_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('report_type', sa.String(length=50), nullable=False),
            sa.Column('period_start', sa.Date(), nullable=False),
            sa.Column('period_end', sa.Date(), nullable=False),
            sa.Column('report_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_historical_reports_user_type', 'historical_reports', ['user_id', 'report_type'], unique=False)
        op.create_index('idx_historical_reports_period', 'historical_reports', ['period_start', 'period_end'], unique=False)

    # From 148457af5653: Add is_admin field to users
    if not column_exists('users', 'is_admin'):
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
        # Set admin user
        op.execute("UPDATE users SET is_admin = 1 WHERE email = 'mhmtsoylu1928@gmail.com'")

    # From 55cc2f92ab12: Add user_feedback table
    if not table_exists('user_feedback'):
        op.create_table('user_feedback',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('feedback_type', sa.String(length=20), nullable=False),
            sa.Column('subject', sa.String(length=200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=True),
            sa.Column('admin_response', sa.Text(), nullable=True),
            sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_user_feedback_id', 'user_feedback', ['id'], unique=False)
        op.create_index('idx_user_feedback_user', 'user_feedback', ['user_id'], unique=False)
        op.create_index('idx_user_feedback_type', 'user_feedback', ['feedback_type'], unique=False)
        op.create_index('idx_user_feedback_resolved', 'user_feedback', ['is_resolved'], unique=False)
        op.create_index('idx_user_feedback_created', 'user_feedback', ['created_at'], unique=False)


def downgrade() -> None:
    # Reverse all changes
    if table_exists('user_feedback'):
        op.drop_table('user_feedback')
    if column_exists('users', 'is_admin'):
        op.drop_column('users', 'is_admin')
    if table_exists('historical_reports'):
        op.drop_table('historical_reports')
    if column_exists('entries', 'payment_history_id'):
        op.drop_constraint('fk_entries_payment_history', 'entries', type_='foreignkey')
        op.drop_column('entries', 'payment_history_id')
    if table_exists('payment_history'):
        op.drop_table('payment_history')
    if table_exists('recurring_payments'):
        op.drop_table('recurring_payments')

    # Drop indexes
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('entries')]
    if 'idx_entries_date_range' in existing_indexes:
        op.drop_index('idx_entries_date_range', table_name='entries')
    if 'idx_entries_category' in existing_indexes:
        op.drop_index('idx_entries_category', table_name='entries')
    if 'idx_entries_user_date' in existing_indexes:
        op.drop_index('idx_entries_user_date', table_name='entries')

    # Drop AI columns
    if column_exists('entries', 'ai_processed'):
        op.drop_column('entries', 'ai_processed')
    if column_exists('entries', 'location_data'):
        op.drop_column('entries', 'location_data')
    if column_exists('entries', 'merchant_name'):
        op.drop_column('entries', 'merchant_name')
    if column_exists('entries', 'ai_confidence_score'):
        op.drop_column('entries', 'ai_confidence_score')
    if column_exists('entries', 'ai_suggested_category_id'):
        op.drop_column('entries', 'ai_suggested_category_id')
