"""Character - added image variations

Revision ID: 9a29030d70a4
Revises: 13080903d4a3
Create Date: 2025-04-20 19:36:27.198287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a29030d70a4'
down_revision: Union[str, None] = '13080903d4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
