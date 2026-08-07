"""Add place_name and place_country to trips

Revision ID: a1b2c3d4e5f6
Revises: d3edd248919b
Create Date: 2026-08-07 08:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd3edd248919b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add place_name and place_country nullable columns to trips table."""
    op.add_column('trips', sa.Column('place_name', sa.String(length=300), nullable=True))
    op.add_column('trips', sa.Column('place_country', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Remove place_name and place_country columns from trips table."""
    op.drop_column('trips', 'place_country')
    op.drop_column('trips', 'place_name')
