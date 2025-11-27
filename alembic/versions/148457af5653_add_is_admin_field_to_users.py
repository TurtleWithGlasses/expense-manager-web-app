"""add_is_admin_field_to_users

Revision ID: 148457af5653
Revises: 91bdbf9e0309
Create Date: 2025-11-27 16:18:23.149830

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '148457af5653'
down_revision = '91bdbf9e0309'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))

    # Set mhmtsoylu1928@gmail.com as admin
    op.execute("UPDATE users SET is_admin = 1 WHERE email = 'mhmtsoylu1928@gmail.com'")


def downgrade() -> None:
    # Remove is_admin column
    op.drop_column('users', 'is_admin')