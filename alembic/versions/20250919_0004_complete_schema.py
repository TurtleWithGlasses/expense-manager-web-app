from alembic import op
import sqlalchemy as sa

revision = '20250919_0004_complete_schema'
down_revision = '20250919_0002_user_preferences'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop existing tables if they exist (to start fresh)
    op.execute("DROP TABLE IF EXISTS entries CASCADE")
    op.execute("DROP TABLE IF EXISTS categories CASCADE") 
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
    )

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    )

    # Create entries table with ALL columns
    op.create_table(
        'entries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(16), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('note', sa.String(255), nullable=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('description', sa.String(), nullable=True),  # This was missing!
    )

def downgrade() -> None:
    op.drop_table('entries')
    op.drop_table('categories')
    op.drop_table('users')