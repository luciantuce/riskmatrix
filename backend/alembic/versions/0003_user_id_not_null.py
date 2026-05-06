"""set user_id NOT NULL on clients / kit_submissions / kit_results

Revision ID: 0003_user_id_not_null
Revises: 0002_add_users
Create Date: 2026-04-28

After 0002 backfilled all orphan rows under a founder placeholder user,
we now enforce the NOT NULL constraint at the schema level. Any subsequent
INSERT must provide user_id (the application enforces this through
`current_user` dependency on routes).

Safety check: this migration verifies there are no remaining NULLs before
flipping the constraint. If any row has user_id IS NULL, the migration
aborts with a clear error.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_user_id_not_null"
down_revision: Union[str, None] = "0002_add_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_no_nulls(bind, table: str) -> None:
    count = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
    ).scalar_one()
    if count > 0:
        raise RuntimeError(
            f"Cannot SET NOT NULL on {table}.user_id: {count} rows still have user_id=NULL. "
            f"Backfill in 0002 should have handled this. Inspect the data manually "
            f"(SELECT * FROM {table} WHERE user_id IS NULL) and either assign them "
            f"to a user or DELETE them, then re-run this migration."
        )


def upgrade() -> None:
    bind = op.get_bind()

    _assert_no_nulls(bind, "clients")
    _assert_no_nulls(bind, "kit_submissions")
    _assert_no_nulls(bind, "kit_results")

    op.alter_column("clients", "user_id", nullable=False)
    op.alter_column("kit_submissions", "user_id", nullable=False)
    op.alter_column("kit_results", "user_id", nullable=False)


def downgrade() -> None:
    op.alter_column("kit_results", "user_id", nullable=True)
    op.alter_column("kit_submissions", "user_id", nullable=True)
    op.alter_column("clients", "user_id", nullable=True)
