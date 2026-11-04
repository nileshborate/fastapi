"""create courses table

Revision ID: 0001
Revises: 
Create Date: 2026-10-30 11:14:04.012214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False, unique=True),
        sa.Column("price", sa.Double(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("courses")
