"""add level to courses

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-30 11:14:04.517174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "courses",
        sa.Column("level", sa.String(20), nullable=False, server_default="beginner"),   # old rows get "beginner"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("courses", "level")
