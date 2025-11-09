"""add_model_blob_to_ai_models

Revision ID: af4ec7fe5872
Revises: 20251108_0002
Create Date: 2025-11-09 18:11:01.571240

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'af4ec7fe5872'
down_revision = '20251108_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add model_blob column to store serialized ML models
    # Use LargeBinary for both SQLite (BLOB) and PostgreSQL (BYTEA)
    op.add_column('ai_models', sa.Column('model_blob', sa.LargeBinary, nullable=True))


def downgrade() -> None:
    # Remove model_blob column
    op.drop_column('ai_models', 'model_blob')