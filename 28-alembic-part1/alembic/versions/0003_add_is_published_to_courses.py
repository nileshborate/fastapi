"""add is_published to courses

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-30 13:50:45.904871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "courses",
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),   # old rows: not published
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("courses", "is_published")
