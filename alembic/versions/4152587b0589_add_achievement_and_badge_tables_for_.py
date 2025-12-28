"""add_achievement_and_badge_tables_for_gamification

Revision ID: 4152587b0589
Revises: ec677a4daa89
Create Date: 2025-12-28 12:22:11.092075

Phase 1: Foundation & Infrastructure - Gamification System
Creates tables for achievements, badges, and user progress tracking.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4152587b0589'
down_revision = 'ec677a4daa89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables already exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'achievements' not in inspector.get_table_names():
        # Create achievements table
        op.create_table(
            'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tier', sa.String(length=20), nullable=True),
        sa.Column('icon_name', sa.String(length=100), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True, default=0),
        sa.Column('unlock_criteria', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_secret', sa.Boolean(), nullable=True, default=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_achievements_id', 'achievements', ['id'], unique=False)
        op.create_index('ix_achievements_code', 'achievements', ['code'], unique=True)

    if 'user_achievements' not in inspector.get_table_names():
        # Create user_achievements table
        op.create_table(
            'user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('progress_data', sa.JSON(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_new', sa.Boolean(), nullable=True, default=True),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_user_achievements_id', 'user_achievements', ['id'], unique=False)
        op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'], unique=False)
        op.create_index('ix_user_achievements_earned_at', 'user_achievements', ['earned_at'], unique=False)

    if 'badges' not in inspector.get_table_names():
        # Create badges table
        op.create_table(
            'badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('rarity', sa.String(length=20), nullable=True),
        sa.Column('requirement_type', sa.String(length=50), nullable=True),
        sa.Column('requirement_data', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_displayable', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_badges_id', 'badges', ['id'], unique=False)
        op.create_index('ix_badges_code', 'badges', ['code'], unique=True)

    if 'user_badges' not in inspector.get_table_names():
        # Create user_badges table
        op.create_table(
            'user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('is_equipped', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_new', sa.Boolean(), nullable=True, default=True),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.Column('equipped_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_user_badges_id', 'user_badges', ['id'], unique=False)
        op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'], unique=False)
        op.create_index('ix_user_badges_earned_at', 'user_badges', ['earned_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign keys)
    op.drop_index('ix_user_badges_earned_at', table_name='user_badges')
    op.drop_index('ix_user_badges_user_id', table_name='user_badges')
    op.drop_index('ix_user_badges_id', table_name='user_badges')
    op.drop_table('user_badges')

    op.drop_index('ix_badges_code', table_name='badges')
    op.drop_index('ix_badges_id', table_name='badges')
    op.drop_table('badges')

    op.drop_index('ix_user_achievements_earned_at', table_name='user_achievements')
    op.drop_index('ix_user_achievements_user_id', table_name='user_achievements')
    op.drop_index('ix_user_achievements_id', table_name='user_achievements')
    op.drop_table('user_achievements')

    op.drop_index('ix_achievements_code', table_name='achievements')
    op.drop_index('ix_achievements_id', table_name='achievements')
    op.drop_table('achievements')