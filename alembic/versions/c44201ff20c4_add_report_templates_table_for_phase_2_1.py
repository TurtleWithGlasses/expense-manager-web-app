"""Add report templates table for Phase 2.1

Revision ID: c44201ff20c4
Revises: 51db7707995a
Create Date: 2025-12-29 00:22:28.292620

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c44201ff20c4'
down_revision = '51db7707995a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('date_range_type', sa.String(length=50), nullable=False, server_default='custom'),
        sa.Column('custom_days', sa.Integer(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('default_export_format', sa.String(length=20), nullable=False, server_default='excel'),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_templates_id'), 'report_templates', ['id'], unique=False)
    op.create_index(op.f('ix_report_templates_user_id'), 'report_templates', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_report_templates_user_id'), table_name='report_templates')
    op.drop_index(op.f('ix_report_templates_id'), table_name='report_templates')
    op.drop_table('report_templates')