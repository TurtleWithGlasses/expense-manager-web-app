"""add_ai_fields_to_entries

Revision ID: 91bdbf9e0309
Revises: 7dfb33c43cde
Create Date: 2025-11-16 12:07:13.378842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91bdbf9e0309'
down_revision = '7dfb33c43cde'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI-related columns to entries table
    # Note: Not adding foreign key constraint for SQLite compatibility
    op.add_column('entries', sa.Column('ai_suggested_category_id', sa.Integer(), nullable=True))
    op.add_column('entries', sa.Column('ai_confidence_score', sa.Numeric(precision=3, scale=2), nullable=True))
    op.add_column('entries', sa.Column('merchant_name', sa.String(length=255), nullable=True))
    op.add_column('entries', sa.Column('location_data', sa.String(), nullable=True))
    op.add_column('entries', sa.Column('ai_processed', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Drop AI-related columns
    op.drop_column('entries', 'ai_processed')
    op.drop_column('entries', 'location_data')
    op.drop_column('entries', 'merchant_name')
    op.drop_column('entries', 'ai_confidence_score')
    op.drop_column('entries', 'ai_suggested_category_id')