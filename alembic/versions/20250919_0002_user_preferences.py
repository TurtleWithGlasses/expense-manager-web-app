from alembic import op
import sqlalchemy as sa

revision = '20250919_0002_user_preferences'
down_revision = '20250902_0001_init'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('currency_code', sa.String(3), nullable=True, default='USD'),
        sa.Column('preferences', sa.JSON, nullable=True, default=dict)
    )

def downgrade() -> None:
    op.drop_table('user_preferences')