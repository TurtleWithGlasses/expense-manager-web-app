from alembic import op
import sqlalchemy as sa

revision = 'add_currency_to_entries'
down_revision = '20250919_0004_complete_schema'  # This should be your last migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('entries', sa.Column('currency_code', sa.String(3), nullable=False, server_default='USD'))

def downgrade() -> None:
    op.drop_column('entries', 'currency_code')