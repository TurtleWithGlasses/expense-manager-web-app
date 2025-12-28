"""Phase 3: Add XP and Level to User

Revision ID: 51db7707995a
Revises: 4152587b0589
Create Date: 2025-12-28 13:53:37.861726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51db7707995a'
down_revision = '4152587b0589'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add xp and level columns to users table
    op.add_column('users', sa.Column('xp', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove xp and level columns from users table
    op.drop_column('users', 'level')
    op.drop_column('users', 'xp')