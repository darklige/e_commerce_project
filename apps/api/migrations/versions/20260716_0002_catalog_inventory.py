"""create catalog and inventory tables

Revision ID: 20260716_0002
Revises: 20260716_0001
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260716_0002"
down_revision: str | None = "20260716_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_is_active", "categories", ["is_active"])
    op.create_index("ix_categories_sort_order", "categories", ["sort_order"])

    op.create_table(
        "brands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brands_name", "brands", ["name"])
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=True)
    op.create_index("ix_brands_is_active", "brands", ["is_active"])

    op.create_table(
        "spus",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=180), nullable=False),
        sa.Column("subtitle", sqlmodel.sql.sqltypes.AutoString(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("main_image_url", sqlmodel.sql.sqltypes.AutoString(length=600), nullable=True),
        sa.Column("min_price_cents", sa.Integer(), nullable=False),
        sa.Column("max_price_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_spus_merchant_id", "spus", ["merchant_id"])
    op.create_index("ix_spus_category_id", "spus", ["category_id"])
    op.create_index("ix_spus_brand_id", "spus", ["brand_id"])
    op.create_index("ix_spus_title", "spus", ["title"])
    op.create_index("ix_spus_status", "spus", ["status"])
    op.create_index("ix_spus_min_price_cents", "spus", ["min_price_cents"])

    op.create_table(
        "skus",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("spu_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("sku_code", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("spec_name", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("list_price_cents", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["spu_id"], ["spus.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "sku_code"),
    )
    op.create_index("ix_skus_spu_id", "skus", ["spu_id"])
    op.create_index("ix_skus_merchant_id", "skus", ["merchant_id"])
    op.create_index("ix_skus_sku_code", "skus", ["sku_code"])
    op.create_index("ix_skus_price_cents", "skus", ["price_cents"])
    op.create_index("ix_skus_is_active", "skus", ["is_active"])

    op.create_table(
        "sku_inventory",
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("on_hand", sa.Integer(), nullable=False),
        sa.Column("reserved", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"]),
        sa.PrimaryKeyConstraint("sku_id"),
    )
    op.create_index("ix_sku_inventory_merchant_id", "sku_inventory", ["merchant_id"])

    op.create_table(
        "inventory_reservations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "idempotency_key"),
    )
    op.create_index("ix_inventory_reservations_sku_id", "inventory_reservations", ["sku_id"])
    op.create_index(
        "ix_inventory_reservations_merchant_id",
        "inventory_reservations",
        ["merchant_id"],
    )
    op.create_index(
        "ix_inventory_reservations_idempotency_key",
        "inventory_reservations",
        ["idempotency_key"],
    )
    op.create_index("ix_inventory_reservations_status", "inventory_reservations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_inventory_reservations_status", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_idempotency_key", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_merchant_id", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_sku_id", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")
    op.drop_index("ix_sku_inventory_merchant_id", table_name="sku_inventory")
    op.drop_table("sku_inventory")
    op.drop_index("ix_skus_is_active", table_name="skus")
    op.drop_index("ix_skus_price_cents", table_name="skus")
    op.drop_index("ix_skus_sku_code", table_name="skus")
    op.drop_index("ix_skus_merchant_id", table_name="skus")
    op.drop_index("ix_skus_spu_id", table_name="skus")
    op.drop_table("skus")
    op.drop_index("ix_spus_min_price_cents", table_name="spus")
    op.drop_index("ix_spus_status", table_name="spus")
    op.drop_index("ix_spus_title", table_name="spus")
    op.drop_index("ix_spus_brand_id", table_name="spus")
    op.drop_index("ix_spus_category_id", table_name="spus")
    op.drop_index("ix_spus_merchant_id", table_name="spus")
    op.drop_table("spus")
    op.drop_index("ix_brands_is_active", table_name="brands")
    op.drop_index("ix_brands_slug", table_name="brands")
    op.drop_index("ix_brands_name", table_name="brands")
    op.drop_table("brands")
    op.drop_index("ix_categories_sort_order", table_name="categories")
    op.drop_index("ix_categories_is_active", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
