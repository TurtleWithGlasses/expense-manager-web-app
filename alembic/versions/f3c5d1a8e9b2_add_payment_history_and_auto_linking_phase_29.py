"""Add payment history and auto-linking models (Phase 29)

Revision ID: f3c5d1a8e9b2
Revises: ae483fa17f81
Create Date: 2025-11-24 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f3c5d1a8e9b2'
down_revision = 'ae483fa17f81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_occurrences table
    op.create_table(
        'payment_occurrences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recurring_payment_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=False),
        sa.Column('is_skipped', sa.Boolean(), nullable=False),
        sa.Column('is_late', sa.Boolean(), nullable=False),
        sa.Column('linked_entry_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('confirmation_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_entry_id'], ['entries.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_payment_occurrences_user_id'), 'payment_occurrences', ['user_id'], unique=False)
    op.create_index(op.f('ix_payment_occurrences_recurring_payment_id'), 'payment_occurrences', ['recurring_payment_id'], unique=False)
    op.create_index(op.f('ix_payment_occurrences_scheduled_date'), 'payment_occurrences', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_payment_occurrences_linked_entry_id'), 'payment_occurrences', ['linked_entry_id'], unique=False)

    # Create payment_link_suggestions table
    op.create_table(
        'payment_link_suggestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recurring_payment_id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('match_reason', sa.Text(), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False),
        sa.Column('is_accepted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entry_id'], ['entries.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_payment_link_suggestions_user_id'), 'payment_link_suggestions', ['user_id'], unique=False)
    op.create_index(op.f('ix_payment_link_suggestions_recurring_payment_id'), 'payment_link_suggestions', ['recurring_payment_id'], unique=False)
    op.create_index(op.f('ix_payment_link_suggestions_entry_id'), 'payment_link_suggestions', ['entry_id'], unique=False)
    op.create_index(op.f('ix_payment_link_suggestions_created_at'), 'payment_link_suggestions', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop payment_link_suggestions table
    op.drop_index(op.f('ix_payment_link_suggestions_created_at'), table_name='payment_link_suggestions')
    op.drop_index(op.f('ix_payment_link_suggestions_entry_id'), table_name='payment_link_suggestions')
    op.drop_index(op.f('ix_payment_link_suggestions_recurring_payment_id'), table_name='payment_link_suggestions')
    op.drop_index(op.f('ix_payment_link_suggestions_user_id'), table_name='payment_link_suggestions')
    op.drop_table('payment_link_suggestions')

    # Drop payment_occurrences table
    op.drop_index(op.f('ix_payment_occurrences_linked_entry_id'), table_name='payment_occurrences')
    op.drop_index(op.f('ix_payment_occurrences_scheduled_date'), table_name='payment_occurrences')
    op.drop_index(op.f('ix_payment_occurrences_recurring_payment_id'), table_name='payment_occurrences')
    op.drop_index(op.f('ix_payment_occurrences_user_id'), table_name='payment_occurrences')
    op.drop_table('payment_occurrences')
