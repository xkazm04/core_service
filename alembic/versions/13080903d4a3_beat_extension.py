"""Beat extension

Revision ID: 13080903d4a3
Revises: 0433a35c69d1
Create Date: 2025-04-19 18:42:52.064491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13080903d4a3'
down_revision: Union[str, None] = '0433a35c69d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
