from alembic import op
import sqlalchemy as sa


revision = '20250902_0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
    'users',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
    sa.Column('hashed_password', sa.String(255), nullable=False),
    sa.Column('full_name', sa.String(255), nullable=True),
    )


    op.create_table(
    'categories',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(100), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    )


    op.create_table(
    'entries',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
    sa.Column('type', sa.String(16), nullable=False),
    sa.Column('amount', sa.Numeric(12, 2), nullable=False),
    sa.Column('note', sa.String(255), nullable=True),
    sa.Column('date', sa.Date, nullable=False),
    )



def downgrade() -> None:
    op.drop_table('entries')
    op.drop_table('categories')
    op.drop_table('users')