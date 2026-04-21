"""Add telegram_users and telegram_link_tokens tables (Phase F)

Revision ID: 20260421_0001
Revises: 20260410_0001
Create Date: 2026-04-21
"""
from alembic import op

revision = "20260421_0001"
down_revision = "20260410_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            id                SERIAL PRIMARY KEY,
            user_id           INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            telegram_user_id  BIGINT  NOT NULL UNIQUE,
            telegram_username VARCHAR(255),
            linked_at         TIMESTAMP NOT NULL DEFAULT NOW(),
            last_entry_id     INTEGER REFERENCES entries(id) ON DELETE SET NULL,
            last_entry_at     TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_telegram_users_telegram_user_id "
        "ON telegram_users (telegram_user_id)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS telegram_link_tokens (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token      VARCHAR(10) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used       BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_telegram_link_tokens_token "
        "ON telegram_link_tokens (token)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS telegram_users")
    op.execute("DROP TABLE IF EXISTS telegram_link_tokens")
