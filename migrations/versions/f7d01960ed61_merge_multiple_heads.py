"""Merge multiple heads

Revision ID: f7d01960ed61
Revises: 44e842aa43fb, e99844638511
Create Date: 2025-10-03 14:45:02.410953

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7d01960ed61'
down_revision = ('44e842aa43fb', 'e99844638511')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
