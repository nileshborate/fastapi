"""rename price to fee

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-30 13:53:56.968652

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
    # autogenerate wrote: add_column("fee") + drop_column("price") - that DELETES every price!
    # A rename must be written by hand:
    with op.batch_alter_table("courses") as batch_op:
        batch_op.alter_column("price", new_column_name="fee")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("courses") as batch_op:
        batch_op.alter_column("fee", new_column_name="price")
