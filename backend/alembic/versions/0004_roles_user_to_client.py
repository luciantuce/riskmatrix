"""normalize user roles to client/admin/super_admin

Revision ID: 0004_roles_user_to_client
Revises: 0003_user_id_not_null
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_roles_user_to_client"
down_revision: Union[str, None] = "0003_user_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE users SET role = 'client' WHERE role = 'user'"))
    op.alter_column("users", "role", server_default="client")


def downgrade() -> None:
    op.execute(sa.text("UPDATE users SET role = 'user' WHERE role = 'client'"))
    op.alter_column("users", "role", server_default="user")
