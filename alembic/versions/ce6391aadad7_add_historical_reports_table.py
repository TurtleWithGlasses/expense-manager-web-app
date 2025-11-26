"""add_historical_reports_table

Revision ID: ce6391aadad7
Revises: f3c5d1a8e9b2
Create Date: 2025-11-26 16:51:01.427848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce6391aadad7'
down_revision = 'f3c5d1a8e9b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create historical_reports table
    op.create_table(
        'historical_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=20), nullable=False),
        sa.Column('report_period', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('report_data', sa.Text(), nullable=False),
        sa.Column('total_income', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_expenses', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('net_savings', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('transaction_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('currency_code', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_historical_reports_id', 'historical_reports', ['id'])
    op.create_index('ix_historical_reports_user_id', 'historical_reports', ['user_id'])
    op.create_index('ix_historical_reports_report_type', 'historical_reports', ['report_type'])
    op.create_index('ix_historical_reports_report_period', 'historical_reports', ['report_period'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_historical_reports_report_period', table_name='historical_reports')
    op.drop_index('ix_historical_reports_report_type', table_name='historical_reports')
    op.drop_index('ix_historical_reports_user_id', table_name='historical_reports')
    op.drop_index('ix_historical_reports_id', table_name='historical_reports')

    # Drop table
    op.drop_table('historical_reports')