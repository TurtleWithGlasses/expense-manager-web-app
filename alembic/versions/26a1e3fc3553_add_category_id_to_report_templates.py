"""Add category_id to report_templates

Revision ID: 26a1e3fc3553
Revises: c44201ff20c4
Create Date: 2025-12-29 11:38:56.769567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26a1e3fc3553'
down_revision = 'c44201ff20c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_report_templates_category_id',
            'categories',
            ['category_id'], ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index('ix_report_templates_category_id', ['category_id'])


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.drop_index('ix_report_templates_category_id')
        batch_op.drop_constraint('fk_report_templates_category_id', type_='foreignkey')
        batch_op.drop_column('category_id')