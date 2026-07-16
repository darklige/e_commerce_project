"""create cart order and payment tables

Revision ID: 20260716_0003
Revises: 20260716_0002
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260716_0003"
down_revision: str | None = "20260716_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_id", "sku_id"),
    )
    op.create_index("ix_cart_items_customer_id", "cart_items", ["customer_id"])
    op.create_index("ix_cart_items_sku_id", "cart_items", ["sku_id"])
    op.create_index("ix_cart_items_selected", "cart_items", ["selected"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_no", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("request_signature", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("items_total_cents", sa.Integer(), nullable=False),
        sa.Column("shipping_fee_cents", sa.Integer(), nullable=False),
        sa.Column("payable_total_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sqlmodel.sql.sqltypes.AutoString(length=8), nullable=False),
        sa.Column("receiver_name", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("receiver_phone", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("shipping_address", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("close_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("close_note", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_id", "idempotency_key"),
    )
    op.create_index("ix_orders_order_no", "orders", ["order_no"], unique=True)
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])
    op.create_index("ix_orders_close_reason", "orders", ["close_reason"])
    op.create_index("ix_orders_paid_at", "orders", ["paid_at"])
    op.create_index("ix_orders_expires_at", "orders", ["expires_at"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("reservation_id", sa.Uuid(), nullable=False),
        sa.Column("product_title", sqlmodel.sql.sqltypes.AutoString(length=180), nullable=False),
        sa.Column("sku_spec_name", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("sku_code", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("product_image_url", sqlmodel.sql.sqltypes.AutoString(length=600), nullable=True),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["spus.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["inventory_reservations.id"]),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_customer_id", "order_items", ["customer_id"])
    op.create_index("ix_order_items_merchant_id", "order_items", ["merchant_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_index("ix_order_items_sku_id", "order_items", ["sku_id"])
    op.create_index("ix_order_items_reservation_id", "order_items", ["reservation_id"])

    op.create_table(
        "order_status_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("from_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("to_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("action", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_status_events_order_id", "order_status_events", ["order_id"])
    op.create_index(
        "ix_order_status_events_actor_user_id",
        "order_status_events",
        ["actor_user_id"],
    )
    op.create_index("ix_order_status_events_from_status", "order_status_events", ["from_status"])
    op.create_index("ix_order_status_events_to_status", "order_status_events", ["to_status"])
    op.create_index("ix_order_status_events_action", "order_status_events", ["action"])
    op.create_index("ix_order_status_events_created_at", "order_status_events", ["created_at"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("provider_trade_no", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("failure_reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "idempotency_key"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])
    op.create_index("ix_payments_provider", "payments", ["provider"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"])
    op.create_index("ix_payments_provider_trade_no", "payments", ["provider_trade_no"])
    op.create_index("ix_payments_paid_at", "payments", ["paid_at"])
    op.create_index("ix_payments_created_at", "payments", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_payments_created_at", table_name="payments")
    op.drop_index("ix_payments_paid_at", table_name="payments")
    op.drop_index("ix_payments_provider_trade_no", table_name="payments")
    op.drop_index("ix_payments_idempotency_key", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_provider", table_name="payments")
    op.drop_index("ix_payments_customer_id", table_name="payments")
    op.drop_index("ix_payments_order_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_order_status_events_created_at", table_name="order_status_events")
    op.drop_index("ix_order_status_events_action", table_name="order_status_events")
    op.drop_index("ix_order_status_events_to_status", table_name="order_status_events")
    op.drop_index("ix_order_status_events_from_status", table_name="order_status_events")
    op.drop_index("ix_order_status_events_actor_user_id", table_name="order_status_events")
    op.drop_index("ix_order_status_events_order_id", table_name="order_status_events")
    op.drop_table("order_status_events")

    op.drop_index("ix_order_items_reservation_id", table_name="order_items")
    op.drop_index("ix_order_items_sku_id", table_name="order_items")
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_merchant_id", table_name="order_items")
    op.drop_index("ix_order_items_customer_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_expires_at", table_name="orders")
    op.drop_index("ix_orders_paid_at", table_name="orders")
    op.drop_index("ix_orders_close_reason", table_name="orders")
    op.drop_index("ix_orders_idempotency_key", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_index("ix_orders_order_no", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_cart_items_selected", table_name="cart_items")
    op.drop_index("ix_cart_items_sku_id", table_name="cart_items")
    op.drop_index("ix_cart_items_customer_id", table_name="cart_items")
    op.drop_table("cart_items")
