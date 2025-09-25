"""Add AI features

Revision ID: 20250102_0001_add_ai_features
Revises: 20250919_0004_complete_schema
Create Date: 2025-01-02 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250102_0001_add_ai_features'
down_revision = 'add_email_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create AI models table
    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('accuracy_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('training_data_count', sa.Integer(), nullable=True),
        sa.Column('last_trained', sa.DateTime(), nullable=True),
        sa.Column('model_parameters', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create AI suggestions table
    op.create_table(
        'ai_suggestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=True),
        sa.Column('suggested_category_id', sa.Integer(), nullable=True),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('suggestion_data', sa.Text(), nullable=True),
        sa.Column('is_accepted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('feedback_updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entry_id'], ['entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['suggested_category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user AI preferences table
    op.create_table(
        'user_ai_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('auto_categorization_enabled', sa.Boolean(), nullable=True),
        sa.Column('smart_suggestions_enabled', sa.Boolean(), nullable=True),
        sa.Column('spending_insights_enabled', sa.Boolean(), nullable=True),
        sa.Column('budget_predictions_enabled', sa.Boolean(), nullable=True),
        sa.Column('min_confidence_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('auto_accept_threshold', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('learn_from_feedback', sa.Boolean(), nullable=True),
        sa.Column('retrain_frequency_days', sa.Integer(), nullable=True),
        sa.Column('share_anonymized_data', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    # Drop AI tables in reverse order
    op.drop_table('user_ai_preferences')
    op.drop_table('ai_suggestions')
    op.drop_table('ai_models')
