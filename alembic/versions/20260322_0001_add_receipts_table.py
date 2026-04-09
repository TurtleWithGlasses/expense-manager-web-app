"""Add receipts table for Phase A - receipt persistence

Revision ID: 20260322_0001
Revises: 20260101_0001
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = '20260322_0001'
down_revision = '20260101_0001'
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        op.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                entry_id    INTEGER REFERENCES entries(id) ON DELETE SET NULL,
                image_data  TEXT,
                ocr_text    TEXT,
                extracted_data TEXT,
                confidence  VARCHAR(16),
                merchant    VARCHAR(255),
                amount      NUMERIC(12,2),
                receipt_date DATE,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_receipts_user_id ON receipts (user_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_receipts_entry_id ON receipts (entry_id)")
    else:
        op.create_table(
            'receipts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('entry_id', sa.Integer(), sa.ForeignKey('entries.id', ondelete='SET NULL'), nullable=True),
            sa.Column('image_data', sa.Text(), nullable=True),
            sa.Column('ocr_text', sa.Text(), nullable=True),
            sa.Column('extracted_data', sa.Text(), nullable=True),
            sa.Column('confidence', sa.String(16), nullable=True),
            sa.Column('merchant', sa.String(255), nullable=True),
            sa.Column('amount', sa.Numeric(12, 2), nullable=True),
            sa.Column('receipt_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_receipts_user_id', 'receipts', ['user_id'])
        op.create_index('ix_receipts_entry_id', 'receipts', ['entry_id'])


def downgrade() -> None:
    op.drop_table('receipts')
