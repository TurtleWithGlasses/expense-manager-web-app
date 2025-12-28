"""add scenarios tables for what-if analysis

Revision ID: 20250125_0002
Revises: 20250125_0001
Create Date: 2025-01-25 01:00:00.000000

Phase 4: Advanced ML Features - Scenario Planning
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '20250125_0002'
down_revision = '20250125_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'scenarios' not in inspector.get_table_names():
        # Create scenarios table
        op.create_table(
            'scenarios',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scenario_type', sa.String(length=50), nullable=False),
            sa.Column('parameters', JSON, nullable=False),
            sa.Column('projected_outcome', JSON, nullable=True),
            sa.Column('baseline_data', JSON, nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes for scenarios table
        op.create_index('ix_scenarios_id', 'scenarios', ['id'])
        op.create_index('ix_scenarios_user_id', 'scenarios', ['user_id'])
        op.create_index('ix_scenarios_scenario_type', 'scenarios', ['scenario_type'])
        op.create_index('ix_scenarios_created_at', 'scenarios', ['created_at'])
        op.create_index('ix_scenarios_is_active', 'scenarios', ['is_active'])
        op.create_index('ix_scenarios_is_favorite', 'scenarios', ['is_favorite'])

        # Composite index for common queries
        op.create_index(
            'ix_scenarios_user_type_active',
            'scenarios',
            ['user_id', 'scenario_type', 'is_active']
        )

    if 'scenario_comparisons' not in inspector.get_table_names():
        # Create scenario_comparisons table
        op.create_table(
            'scenario_comparisons',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scenario_ids', JSON, nullable=False),
            sa.Column('comparison_data', JSON, nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes for scenario_comparisons table
        op.create_index('ix_scenario_comparisons_id', 'scenario_comparisons', ['id'])
        op.create_index('ix_scenario_comparisons_user_id', 'scenario_comparisons', ['user_id'])
        op.create_index('ix_scenario_comparisons_created_at', 'scenario_comparisons', ['created_at'])


def downgrade() -> None:
    # Drop scenario_comparisons table indexes
    op.drop_index('ix_scenario_comparisons_created_at', table_name='scenario_comparisons')
    op.drop_index('ix_scenario_comparisons_user_id', table_name='scenario_comparisons')
    op.drop_index('ix_scenario_comparisons_id', table_name='scenario_comparisons')

    # Drop scenario_comparisons table
    op.drop_table('scenario_comparisons')

    # Drop scenarios table indexes
    op.drop_index('ix_scenarios_user_type_active', table_name='scenarios')
    op.drop_index('ix_scenarios_is_favorite', table_name='scenarios')
    op.drop_index('ix_scenarios_is_active', table_name='scenarios')
    op.drop_index('ix_scenarios_created_at', table_name='scenarios')
    op.drop_index('ix_scenarios_scenario_type', table_name='scenarios')
    op.drop_index('ix_scenarios_user_id', table_name='scenarios')
    op.drop_index('ix_scenarios_id', table_name='scenarios')

    # Drop scenarios table
    op.drop_table('scenarios')
