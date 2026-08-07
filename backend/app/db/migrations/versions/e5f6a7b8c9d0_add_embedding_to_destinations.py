"""Add embedding vector column to destinations table

Revision ID: e5f6a7b8c9d0
Revises: a1b2c3d4e5f6
Create Date: 2026-08-07 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add embedding vector column to destinations table."""
    op.add_column('destinations', sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True))


def downgrade() -> None:
    """Remove embedding column from destinations table."""
    op.drop_column('destinations', 'embedding')
