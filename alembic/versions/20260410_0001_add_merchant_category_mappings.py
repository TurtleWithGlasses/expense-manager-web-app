"""Add merchant_category_mappings table (Phase E)

Revision ID: 20260410_0001
Revises: 20260322_0001
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = "20260410_0001"
down_revision = "20260322_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS merchant_category_mappings (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            merchant_key VARCHAR(255) NOT NULL,
            category_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            use_count    INTEGER NOT NULL DEFAULT 1,
            last_used    TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_user_merchant_key UNIQUE (user_id, merchant_key)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_merchant_mappings_user_id "
        "ON merchant_category_mappings (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS merchant_category_mappings")
