"""add users + webhook_events tables; add user_id NULLABLE on existing tables

Revision ID: 0002_add_users
Revises: 0001_initial
Create Date: 2026-04-28

This migration adds the auth foundation:
- `users` table (mirror of Clerk identities)
- `webhook_events` table (idempotency log for Clerk + Stripe inbound events)
- `clients.user_id` (NULLABLE for now; tightened in 0003 after backfill)
- `clients.deleted_at` (soft-delete column)
- `kit_submissions.user_id` (NULLABLE)
- `kit_results.user_id` (NULLABLE)

Backfill strategy:
- If the table has zero rows: nothing to do, 0003 will SET NOT NULL directly
- If rows exist: this migration creates a `founder` user with a placeholder
  clerk_user_id and assigns all orphan rows to it. The placeholder MUST be
  replaced with a real clerk_user_id before going to production with real data.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0002_add_users"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLACEHOLDER_CLERK_ID = "placeholder_founder_replace_after_first_real_signup"


def upgrade() -> None:
    # ---- users -------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clerk_user_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint("uq_users_clerk_user_id", "users", ["clerk_user_id"])
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ---- webhook_events ----------------------------------------------------
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source", "external_id", name="uq_webhook_events_source_external"),
    )
    op.create_index(
        "idx_webhook_events_source_received",
        "webhook_events",
        ["source", "received_at"],
    )

    # ---- clients: add user_id NULLABLE + deleted_at -----------------------
    op.add_column("clients", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("clients", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_clients_user_id", "clients", "users", ["user_id"], ["id"],
    )
    op.create_index("ix_clients_user_id", "clients", ["user_id"])
    op.create_index("ix_clients_deleted_at", "clients", ["deleted_at"])

    # ---- kit_submissions: add user_id NULLABLE ----------------------------
    op.add_column("kit_submissions", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_kit_submissions_user_id", "kit_submissions", "users", ["user_id"], ["id"],
    )
    op.create_index("ix_kit_submissions_user_id", "kit_submissions", ["user_id"])

    # ---- kit_results: add user_id NULLABLE --------------------------------
    op.add_column("kit_results", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_kit_results_user_id", "kit_results", "users", ["user_id"], ["id"],
    )
    op.create_index("ix_kit_results_user_id", "kit_results", ["user_id"])

    # ---- backfill: assign orphan rows to a founder user ------------------
    # Only acts if there are existing rows in clients/kit_submissions/kit_results.
    bind = op.get_bind()
    has_data = bind.execute(sa.text("SELECT 1 FROM clients LIMIT 1")).first() is not None
    if has_data:
        bind.execute(
            sa.text(
                """
                INSERT INTO users (clerk_user_id, email, full_name, role)
                VALUES (:clerk_id, :email, :name, 'admin')
                """
            ),
            {
                "clerk_id": PLACEHOLDER_CLERK_ID,
                "email": "founder-placeholder@example.com",
                "name": "Founder (placeholder, replace after real signup)",
            },
        )
        founder_id = bind.execute(
            sa.text("SELECT id FROM users WHERE clerk_user_id = :clerk_id"),
            {"clerk_id": PLACEHOLDER_CLERK_ID},
        ).scalar_one()
        bind.execute(
            sa.text("UPDATE clients SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": founder_id},
        )
        bind.execute(
            sa.text("UPDATE kit_submissions SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": founder_id},
        )
        bind.execute(
            sa.text("UPDATE kit_results SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": founder_id},
        )


def downgrade() -> None:
    op.drop_index("ix_kit_results_user_id", table_name="kit_results")
    op.drop_constraint("fk_kit_results_user_id", "kit_results", type_="foreignkey")
    op.drop_column("kit_results", "user_id")

    op.drop_index("ix_kit_submissions_user_id", table_name="kit_submissions")
    op.drop_constraint("fk_kit_submissions_user_id", "kit_submissions", type_="foreignkey")
    op.drop_column("kit_submissions", "user_id")

    op.drop_index("ix_clients_deleted_at", table_name="clients")
    op.drop_index("ix_clients_user_id", table_name="clients")
    op.drop_constraint("fk_clients_user_id", "clients", type_="foreignkey")
    op.drop_column("clients", "deleted_at")
    op.drop_column("clients", "user_id")

    op.drop_index("idx_webhook_events_source_received", table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_constraint("uq_users_clerk_user_id", "users", type_="unique")
    op.drop_table("users")
