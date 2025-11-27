"""add_user_feedback_table

Revision ID: 55cc2f92ab12
Revises: 148457af5653
Create Date: 2025-11-27 16:20:50.837385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55cc2f92ab12'
down_revision = '148457af5653'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_feedback table
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_user_feedback_id', 'user_feedback', ['id'])
    op.create_index('ix_user_feedback_user_id', 'user_feedback', ['user_id'])
    op.create_index('ix_user_feedback_feedback_type', 'user_feedback', ['feedback_type'])
    op.create_index('ix_user_feedback_is_resolved', 'user_feedback', ['is_resolved'])
    op.create_index('ix_user_feedback_created_at', 'user_feedback', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_feedback_created_at', table_name='user_feedback')
    op.drop_index('ix_user_feedback_is_resolved', table_name='user_feedback')
    op.drop_index('ix_user_feedback_feedback_type', table_name='user_feedback')
    op.drop_index('ix_user_feedback_user_id', table_name='user_feedback')
    op.drop_index('ix_user_feedback_id', table_name='user_feedback')

    # Drop table
    op.drop_table('user_feedback')