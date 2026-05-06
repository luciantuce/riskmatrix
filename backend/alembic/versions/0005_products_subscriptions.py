"""add products, bundle_includes, subscriptions, invoices

Revision ID: 0005_products_subscriptions
Revises: 0004_roles_user_to_client
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_products_subscriptions"
down_revision: Union[str, None] = "0004_roles_user_to_client"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("kit_id", sa.Integer(), sa.ForeignKey("kits.id"), nullable=True),
        sa.Column("stripe_price_id_monthly", sa.String(), nullable=True),
        sa.Column("stripe_price_id_yearly", sa.String(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_products_code", "products", ["code"])
    op.create_index("ix_products_code", "products", ["code"])

    op.create_table(
        "bundle_includes",
        sa.Column(
            "bundle_product_id", sa.Integer(), sa.ForeignKey("products.id"), primary_key=True
        ),
        sa.Column("kit_id", sa.Integer(), sa.ForeignKey("kits.id"), primary_key=True),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("billing_cycle", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"]
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_product_id", "subscriptions", ["product_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=True
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("hosted_invoice_url", sa.String(), nullable=True),
        sa.Column("pdf_url", sa.String(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_invoices_stripe_invoice_id", "invoices", ["stripe_invoice_id"])
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_invoices_user_id", table_name="invoices")
    op.drop_index("ix_invoices_subscription_id", table_name="invoices")
    op.drop_constraint("uq_invoices_stripe_invoice_id", "invoices", type_="unique")
    op.drop_table("invoices")

    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_product_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_constraint("uq_subscriptions_stripe_subscription_id", "subscriptions", type_="unique")
    op.drop_table("subscriptions")

    op.drop_table("bundle_includes")

    op.drop_index("ix_products_code", table_name="products")
    op.drop_constraint("uq_products_code", "products", type_="unique")
    op.drop_table("products")
