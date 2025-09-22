"""Add email verification columns to users table

Revision ID: add_email_verification_columns
Revises: 26999012527c_sync_models_with_database
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_email_verification_columns'
down_revision = '26999012527c_sync_models_with_database'  # Replace with your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns already exist before adding them
    connection = op.get_bind()
    
    # Check if is_verified column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'is_verified'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
        print("✅ Added is_verified column")
    else:
        print("ℹ️  is_verified column already exists")
    
    # Check if verification_token column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'verification_token'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
        print("✅ Added verification_token column")
    else:
        print("ℹ️  verification_token column already exists")
    
    # Check if verification_token_expires column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'verification_token_expires'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
        print("✅ Added verification_token_expires column")
    else:
        print("ℹ️  verification_token_expires column already exists")
    
    # Check if password_reset_token column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_reset_token'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
        print("✅ Added password_reset_token column")
    else:
        print("ℹ️  password_reset_token column already exists")
    
    # Check if password_reset_expires column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_reset_expires'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))
        print("✅ Added password_reset_expires column")
    else:
        print("ℹ️  password_reset_expires column already exists")
    
    # Check if created_at column exists
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'created_at'
    """))
    
    if not result.fetchone():
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        print("✅ Added created_at column")
    else:
        print("ℹ️  created_at column already exists")


def downgrade() -> None:
    # Drop columns if they exist
    connection = op.get_bind()
    
    columns_to_drop = [
        'created_at',
        'password_reset_expires', 
        'password_reset_token',
        'verification_token_expires',
        'verification_token',
        'is_verified'
    ]
    
    for column in columns_to_drop:
        result = connection.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = '{column}'
        """))
        
        if result.fetchone():
            op.drop_column('users', column)
            print(f"✅ Dropped {column} column")
        else:
            print(f"ℹ️  {column} column does not exist")
