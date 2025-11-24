"""Add recurring payments and reminders for user-managed bills and subscriptions

Revision ID: ae483fa17f81
Revises: 9d7fd170f147
Create Date: 2025-11-24 18:29:45.309202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae483fa17f81'
down_revision = '9d7fd170f147'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recurring_payments table
    op.create_table(
        'recurring_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False),
        sa.Column('frequency', sa.Enum('WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY', name='recurrencefrequency'), nullable=False),
        sa.Column('due_day', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('remind_days_before', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_recurring_payments_user_id'), 'recurring_payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_recurring_payments_category_id'), 'recurring_payments', ['category_id'], unique=False)

    # Create payment_reminders table
    op.create_table(
        'payment_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recurring_payment_id', sa.Integer(), nullable=False),
        sa.Column('reminder_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=False),
        sa.Column('paid_entry_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paid_entry_id'], ['entries.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_payment_reminders_user_id'), 'payment_reminders', ['user_id'], unique=False)
    op.create_index(op.f('ix_payment_reminders_recurring_payment_id'), 'payment_reminders', ['recurring_payment_id'], unique=False)
    op.create_index(op.f('ix_payment_reminders_reminder_date'), 'payment_reminders', ['reminder_date'], unique=False)


def downgrade() -> None:
    # Drop payment_reminders table
    op.drop_index(op.f('ix_payment_reminders_reminder_date'), table_name='payment_reminders')
    op.drop_index(op.f('ix_payment_reminders_recurring_payment_id'), table_name='payment_reminders')
    op.drop_index(op.f('ix_payment_reminders_user_id'), table_name='payment_reminders')
    op.drop_table('payment_reminders')

    # Drop recurring_payments table
    op.drop_index(op.f('ix_recurring_payments_category_id'), table_name='recurring_payments')
    op.drop_index(op.f('ix_recurring_payments_user_id'), table_name='recurring_payments')
    op.drop_table('recurring_payments')

    # Drop enum type
    op.execute('DROP TYPE recurrencefrequency')