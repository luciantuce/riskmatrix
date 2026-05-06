"""initial schema — bootstrap from Base.metadata

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-19

This is the baseline migration. It creates the full schema by delegating
to SQLAlchemy's Base.metadata. Every subsequent change to the models MUST
be captured with:

    alembic revision --autogenerate -m "describe the change"

The autogen diff compares live DB state vs. Base.metadata, so as long as
this baseline is applied first, diffs will be clean going forward.
"""

from typing import Sequence, Union

import app.models  # noqa: F401 — registers all models with Base.metadata
from alembic import op
from app.database import Base

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
