"""Add split expense tables for Phase 31 - Social & Collaboration

Revision ID: 20260101_0001
Revises: f3c5d1a8e9b2, 4eab34ce34ce
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20260101_0001'
down_revision = ('f3c5d1a8e9b2', '4eab34ce34ce')  # merge both heads
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    postgres = _is_postgres()

    # ── split_contacts ──────────────────────────────────────────────────────
    if postgres:
        op.execute("""
            CREATE TABLE IF NOT EXISTS split_contacts (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name        VARCHAR(150) NOT NULL,
                email       VARCHAR(255),
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_split_contacts_user_id ON split_contacts (user_id)")
    else:
        op.create_table(
            "split_contacts",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # ── split_expenses ──────────────────────────────────────────────────────
    if postgres:
        op.execute("""
            CREATE TABLE IF NOT EXISTS split_expenses (
                id              SERIAL PRIMARY KEY,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                entry_id        INTEGER REFERENCES entries(id) ON DELETE SET NULL,
                title           VARCHAR(200) NOT NULL,
                total_amount    NUMERIC(12, 2) NOT NULL,
                currency_code   VARCHAR(3) NOT NULL DEFAULT 'USD',
                date            DATE NOT NULL,
                notes           TEXT,
                status          VARCHAR(20) NOT NULL DEFAULT 'open',
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_split_expenses_user_id ON split_expenses (user_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_split_expenses_date ON split_expenses (date)")
    else:
        op.create_table(
            "split_expenses",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("entry_id", sa.Integer, sa.ForeignKey("entries.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency_code", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("date", sa.Date, nullable=False, index=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # ── split_participants ──────────────────────────────────────────────────
    if postgres:
        op.execute("""
            CREATE TABLE IF NOT EXISTS split_participants (
                id                  SERIAL PRIMARY KEY,
                split_expense_id    INTEGER NOT NULL REFERENCES split_expenses(id) ON DELETE CASCADE,
                contact_id          INTEGER REFERENCES split_contacts(id) ON DELETE SET NULL,
                name                VARCHAR(150) NOT NULL,
                amount              NUMERIC(12, 2) NOT NULL,
                is_payer            BOOLEAN NOT NULL DEFAULT FALSE,
                is_settled          BOOLEAN NOT NULL DEFAULT FALSE,
                settled_at          TIMESTAMP
            )
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_split_participants_expense_id ON split_participants (split_expense_id)")
    else:
        op.create_table(
            "split_participants",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("split_expense_id", sa.Integer, sa.ForeignKey("split_expenses.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("contact_id", sa.Integer, sa.ForeignKey("split_contacts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("is_payer", sa.Boolean, nullable=False, server_default="0"),
            sa.Column("is_settled", sa.Boolean, nullable=False, server_default="0"),
            sa.Column("settled_at", sa.DateTime, nullable=True),
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS split_participants")
    op.execute("DROP TABLE IF EXISTS split_expenses")
    op.execute("DROP TABLE IF EXISTS split_contacts")
