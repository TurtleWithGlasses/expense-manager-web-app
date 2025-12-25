"""add forecasts table for Prophet time series forecasting

Revision ID: 20250125_0001
Revises: 766b569daa8d
Create Date: 2025-01-25 00:00:00.000000

Phase 4: Advanced ML Features - Prophet Integration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '20250125_0001'
down_revision = '766b569daa8d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create forecasts table
    op.create_table(
        'forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('forecast_type', sa.String(length=50), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('forecast_horizon_days', sa.Integer(), nullable=False),
        sa.Column('training_data_start', sa.DateTime(), nullable=False),
        sa.Column('training_data_end', sa.DateTime(), nullable=False),
        sa.Column('training_data_points', sa.Integer(), nullable=False),
        sa.Column('forecast_data', JSON, nullable=False),
        sa.Column('summary', JSON, nullable=True),
        sa.Column('insights', JSON, nullable=True),
        sa.Column('model_type', sa.String(length=50), nullable=False, server_default='prophet'),
        sa.Column('model_params', JSON, nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False, server_default='0.95'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('actual_vs_predicted', JSON, nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_forecasts_id', 'forecasts', ['id'])
    op.create_index('ix_forecasts_user_id', 'forecasts', ['user_id'])
    op.create_index('ix_forecasts_forecast_type', 'forecasts', ['forecast_type'])
    op.create_index('ix_forecasts_created_at', 'forecasts', ['created_at'])
    op.create_index('ix_forecasts_is_active', 'forecasts', ['is_active'])

    # Composite index for cache lookups
    op.create_index(
        'ix_forecasts_user_type_active',
        'forecasts',
        ['user_id', 'forecast_type', 'is_active']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_forecasts_user_type_active', table_name='forecasts')
    op.drop_index('ix_forecasts_is_active', table_name='forecasts')
    op.drop_index('ix_forecasts_created_at', table_name='forecasts')
    op.drop_index('ix_forecasts_forecast_type', table_name='forecasts')
    op.drop_index('ix_forecasts_user_id', table_name='forecasts')
    op.drop_index('ix_forecasts_id', table_name='forecasts')

    # Drop table
    op.drop_table('forecasts')
