from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'add_email_verification'
down_revision = 'add_currency_to_entries'  # Replace with your latest migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add email verification fields to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

def downgrade() -> None:
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')