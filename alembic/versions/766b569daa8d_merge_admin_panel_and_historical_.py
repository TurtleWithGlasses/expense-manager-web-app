"""merge admin panel and historical reports branches

Revision ID: 766b569daa8d
Revises: 55cc2f92ab12, ce6391aadad7
Create Date: 2025-11-27 17:15:48.606771

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '766b569daa8d'
down_revision = ('55cc2f92ab12', 'ce6391aadad7')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass