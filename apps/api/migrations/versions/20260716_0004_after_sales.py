"""create after-sales refund and work order tables

Revision ID: 20260716_0004
Revises: 20260716_0003
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260716_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "after_sales_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("after_sales_no", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("order_item_id", sa.Uuid(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("request_signature", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_urls", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("refund_amount_cents", sa.Integer(), nullable=False),
        sa.Column("merchant_response_reason", sa.Text(), nullable=True),
        sa.Column("return_tracking_no", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=True),
        sa.Column("return_carrier", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=True),
        sa.Column("merchant_review_due_at", sa.DateTime(), nullable=False),
        sa.Column("buyer_return_due_at", sa.DateTime(), nullable=True),
        sa.Column("merchant_receipt_due_at", sa.DateTime(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.Column("closed_reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_id", "idempotency_key"),
    )
    op.create_index(
        "ix_after_sales_requests_after_sales_no",
        "after_sales_requests",
        ["after_sales_no"],
        unique=True,
    )
    op.create_index("ix_after_sales_requests_customer_id", "after_sales_requests", ["customer_id"])
    op.create_index("ix_after_sales_requests_merchant_id", "after_sales_requests", ["merchant_id"])
    op.create_index("ix_after_sales_requests_order_id", "after_sales_requests", ["order_id"])
    op.create_index(
        "ix_after_sales_requests_order_item_id",
        "after_sales_requests",
        ["order_item_id"],
    )
    op.create_index("ix_after_sales_requests_type", "after_sales_requests", ["type"])
    op.create_index("ix_after_sales_requests_status", "after_sales_requests", ["status"])
    op.create_index(
        "ix_after_sales_requests_idempotency_key",
        "after_sales_requests",
        ["idempotency_key"],
    )
    op.create_index(
        "ix_after_sales_requests_merchant_review_due_at",
        "after_sales_requests",
        ["merchant_review_due_at"],
    )
    op.create_index(
        "ix_after_sales_requests_buyer_return_due_at",
        "after_sales_requests",
        ["buyer_return_due_at"],
    )
    op.create_index(
        "ix_after_sales_requests_merchant_receipt_due_at",
        "after_sales_requests",
        ["merchant_receipt_due_at"],
    )
    op.create_index("ix_after_sales_requests_refunded_at", "after_sales_requests", ["refunded_at"])
    op.create_index("ix_after_sales_requests_created_at", "after_sales_requests", ["created_at"])

    op.create_table(
        "after_sales_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("after_sales_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("from_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("to_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("action", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=True),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["after_sales_id"], ["after_sales_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("after_sales_id", "idempotency_key"),
    )
    op.create_index(
        "ix_after_sales_events_after_sales_id",
        "after_sales_events",
        ["after_sales_id"],
    )
    op.create_index("ix_after_sales_events_actor_user_id", "after_sales_events", ["actor_user_id"])
    op.create_index("ix_after_sales_events_from_status", "after_sales_events", ["from_status"])
    op.create_index("ix_after_sales_events_to_status", "after_sales_events", ["to_status"])
    op.create_index("ix_after_sales_events_action", "after_sales_events", ["action"])
    op.create_index(
        "ix_after_sales_events_idempotency_key",
        "after_sales_events",
        ["idempotency_key"],
    )
    op.create_index("ix_after_sales_events_created_at", "after_sales_events", ["created_at"])

    op.create_table(
        "refunds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("after_sales_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column(
            "provider_refund_no",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
        ),
        sa.Column("failure_reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["after_sales_id"], ["after_sales_requests.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("after_sales_id", "idempotency_key"),
    )
    op.create_index("ix_refunds_after_sales_id", "refunds", ["after_sales_id"])
    op.create_index("ix_refunds_order_id", "refunds", ["order_id"])
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"])
    op.create_index("ix_refunds_customer_id", "refunds", ["customer_id"])
    op.create_index("ix_refunds_merchant_id", "refunds", ["merchant_id"])
    op.create_index("ix_refunds_status", "refunds", ["status"])
    op.create_index("ix_refunds_idempotency_key", "refunds", ["idempotency_key"])
    op.create_index("ix_refunds_provider_refund_no", "refunds", ["provider_refund_no"])
    op.create_index("ix_refunds_refunded_at", "refunds", ["refunded_at"])
    op.create_index("ix_refunds_created_at", "refunds", ["created_at"])

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_order_no", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("after_sales_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("priority", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("queue", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("assigned_admin_id", sa.Uuid(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["after_sales_id"], ["after_sales_requests.id"]),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_orders_work_order_no", "work_orders", ["work_order_no"], unique=True)
    op.create_index("ix_work_orders_after_sales_id", "work_orders", ["after_sales_id"])
    op.create_index("ix_work_orders_order_id", "work_orders", ["order_id"])
    op.create_index("ix_work_orders_customer_id", "work_orders", ["customer_id"])
    op.create_index("ix_work_orders_merchant_id", "work_orders", ["merchant_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_priority", "work_orders", ["priority"])
    op.create_index("ix_work_orders_queue", "work_orders", ["queue"])
    op.create_index("ix_work_orders_assigned_admin_id", "work_orders", ["assigned_admin_id"])
    op.create_index("ix_work_orders_created_at", "work_orders", ["created_at"])
    op.create_index("ix_work_orders_resolved_at", "work_orders", ["resolved_at"])


def downgrade() -> None:
    op.drop_index("ix_work_orders_resolved_at", table_name="work_orders")
    op.drop_index("ix_work_orders_created_at", table_name="work_orders")
    op.drop_index("ix_work_orders_assigned_admin_id", table_name="work_orders")
    op.drop_index("ix_work_orders_queue", table_name="work_orders")
    op.drop_index("ix_work_orders_priority", table_name="work_orders")
    op.drop_index("ix_work_orders_status", table_name="work_orders")
    op.drop_index("ix_work_orders_merchant_id", table_name="work_orders")
    op.drop_index("ix_work_orders_customer_id", table_name="work_orders")
    op.drop_index("ix_work_orders_order_id", table_name="work_orders")
    op.drop_index("ix_work_orders_after_sales_id", table_name="work_orders")
    op.drop_index("ix_work_orders_work_order_no", table_name="work_orders")
    op.drop_table("work_orders")

    op.drop_index("ix_refunds_created_at", table_name="refunds")
    op.drop_index("ix_refunds_refunded_at", table_name="refunds")
    op.drop_index("ix_refunds_provider_refund_no", table_name="refunds")
    op.drop_index("ix_refunds_idempotency_key", table_name="refunds")
    op.drop_index("ix_refunds_status", table_name="refunds")
    op.drop_index("ix_refunds_merchant_id", table_name="refunds")
    op.drop_index("ix_refunds_customer_id", table_name="refunds")
    op.drop_index("ix_refunds_payment_id", table_name="refunds")
    op.drop_index("ix_refunds_order_id", table_name="refunds")
    op.drop_index("ix_refunds_after_sales_id", table_name="refunds")
    op.drop_table("refunds")

    op.drop_index("ix_after_sales_events_created_at", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_action", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_idempotency_key", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_to_status", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_from_status", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_actor_user_id", table_name="after_sales_events")
    op.drop_index("ix_after_sales_events_after_sales_id", table_name="after_sales_events")
    op.drop_table("after_sales_events")

    op.drop_index("ix_after_sales_requests_created_at", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_refunded_at", table_name="after_sales_requests")
    op.drop_index(
        "ix_after_sales_requests_merchant_receipt_due_at",
        table_name="after_sales_requests",
    )
    op.drop_index("ix_after_sales_requests_buyer_return_due_at", table_name="after_sales_requests")
    op.drop_index(
        "ix_after_sales_requests_merchant_review_due_at",
        table_name="after_sales_requests",
    )
    op.drop_index("ix_after_sales_requests_idempotency_key", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_status", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_type", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_order_item_id", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_order_id", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_merchant_id", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_customer_id", table_name="after_sales_requests")
    op.drop_index("ix_after_sales_requests_after_sales_no", table_name="after_sales_requests")
    op.drop_table("after_sales_requests")
