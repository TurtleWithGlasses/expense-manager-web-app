"""Add financial health scores table for Phase 1.2

Revision ID: 4eab34ce34ce
Revises: 6073e83ae99a
Create Date: 2025-12-30 00:09:37.283914

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4eab34ce34ce'
down_revision = '6073e83ae99a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create financial_health_scores table
    op.create_table(
        'financial_health_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('score_date', sa.Date(), nullable=False),
        sa.Column('savings_rate_score', sa.Integer(), nullable=True),
        sa.Column('expense_consistency_score', sa.Integer(), nullable=True),
        sa.Column('budget_adherence_score', sa.Integer(), nullable=True),
        sa.Column('debt_management_score', sa.Integer(), nullable=True),
        sa.Column('goal_progress_score', sa.Integer(), nullable=True),
        sa.Column('emergency_fund_score', sa.Integer(), nullable=True),
        sa.Column('calculation_data', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('score >= 0 AND score <= 100', name='check_score_range'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'score_date', name='uq_user_score_date')
    )
    op.create_index('ix_financial_health_scores_id', 'financial_health_scores', ['id'], unique=False)
    op.create_index('ix_financial_health_scores_score_date', 'financial_health_scores', ['score_date'], unique=False)
    op.create_index('idx_health_scores_user_date', 'financial_health_scores', ['user_id', 'score_date'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_health_scores_user_date', table_name='financial_health_scores')
    op.drop_index('ix_financial_health_scores_score_date', table_name='financial_health_scores')
    op.drop_index('ix_financial_health_scores_id', table_name='financial_health_scores')

    # Drop table
    op.drop_table('financial_health_scores')