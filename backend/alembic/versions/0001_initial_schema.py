"""Initial BOOKLY schema with all 23 normalized tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-26 16:30:00
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # 2. profiles
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_profiles_email"),
    )
    op.create_index("ix_profiles_email", "profiles", ["email"])

    # 3. user_roles
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("assigned_by", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    # 4. authors
    op.create_table(
        "authors",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("nationality", sa.String(length=80), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("slug", name="uq_authors_slug"),
    )
    op.create_index("ix_authors_name", "authors", ["name"])
    op.create_index("ix_authors_slug", "authors", ["slug"])

    # 5. categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=60), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_slug", "categories", ["slug"])

    # 6. publishers
    op.create_table(
        "publishers",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_publishers_name"),
        sa.UniqueConstraint("slug", name="uq_publishers_slug"),
    )
    op.create_index("ix_publishers_name", "publishers", ["name"])
    op.create_index("ix_publishers_slug", "publishers", ["slug"])

    # 7. books
    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=False),
        sa.Column("publisher_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("pages", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=60), nullable=False, server_default="Español"),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sales_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=False, server_default="0.00"),
        sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["publisher_id"], ["publishers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug", name="uq_books_slug"),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
        sa.CheckConstraint("price >= 0", name="ck_books_price_non_negative"),
        sa.CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_books_discount_range",
        ),
        sa.CheckConstraint("stock >= 0", name="ck_books_stock_non_negative"),
        sa.CheckConstraint("low_stock_threshold >= 0", name="ck_books_low_stock_non_negative"),
        sa.CheckConstraint("pages IS NULL OR pages > 0", name="ck_books_pages_positive"),
        sa.CheckConstraint("sales_count >= 0", name="ck_books_sales_count_non_negative"),
    )
    op.create_index("ix_books_title", "books", ["title"])
    op.create_index("ix_books_slug", "books", ["slug"])
    op.create_index("ix_books_isbn", "books", ["isbn"])
    op.create_index("ix_books_active_featured", "books", ["is_active", "is_featured"])

    # 8. book_authors
    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("author_id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("author_order", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
    )

    # 9. book_categories
    op.create_table(
        "book_categories",
        sa.Column("book_id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category_id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
    )

    # 10. book_images
    op.create_table(
        "book_images",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_book_images_book_id", "book_images", ["book_id"])

    # 11. carts
    op.create_table(
        "carts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_carts_user_id"),
    )
    op.create_index("ix_carts_user_id", "carts", ["user_id"])

    # 12. cart_items
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cart_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),
        sa.CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_index("ix_cart_items_book_id", "cart_items", ["book_id"])

    # 13. favorites
    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "book_id", name="uq_favorite_user_book"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_book_id", "favorites", ["book_id"])

    # 14. addresses
    op.create_table(
        "addresses",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=False, server_default="Casa"),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("street_address", sa.String(length=255), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"])

    # 15. coupons (antes de orders por FK)
    op.create_table(
        "coupons",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_order_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("current_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("code", name="uq_coupons_code"),
        sa.CheckConstraint("discount_type IN ('percentage', 'fixed')", name="ck_coupons_type"),
        sa.CheckConstraint("discount_value > 0", name="ck_coupons_value_positive"),
        sa.CheckConstraint("min_order_amount >= 0", name="ck_coupons_min_order_non_negative"),
        sa.CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_coupons_max_uses_positive"),
        sa.CheckConstraint("current_uses >= 0", name="ck_coupons_current_uses_non_negative"),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"])

    # 16. orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_code", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("address_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("shipping_address_snapshot", sa.JSON(), nullable=False),
        sa.Column("shipping_method", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pendiente"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("coupon_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("stock_restored", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["address_id"], ["addresses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("order_code", name="uq_orders_order_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
        sa.CheckConstraint(
            "status IN ('pendiente', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado')",
            name="ck_orders_status",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_orders_discount_non_negative"),
        sa.CheckConstraint("shipping_cost >= 0", name="ck_orders_shipping_non_negative"),
        sa.CheckConstraint("total >= 0", name="ck_orders_total_non_negative"),
    )
    op.create_index("ix_orders_order_code", "orders", ["order_code"])
    op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    # 17. order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("book_title_snapshot", sa.String(length=250), nullable=False),
        sa.Column("book_isbn_snapshot", sa.String(length=32), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_percent_snapshot", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("final_unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        sa.CheckConstraint("final_unit_price >= 0", name="ck_order_items_final_price_non_negative"),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_book_id", "order_items", ["book_id"])

    # 18. payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("transaction_reference", sa.String(length=64), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("order_id", name="uq_payments_order_id"),
        sa.UniqueConstraint("transaction_reference", name="uq_payments_tx_ref"),
        sa.CheckConstraint(
            "method IN ('tarjeta', 'yape', 'plin', 'contra_entrega')",
            name="ck_payments_method",
        ),
        sa.CheckConstraint(
            "status IN ('pendiente', 'simulado_aprobado', 'fallido', 'reembolsado')",
            name="ck_payments_status",
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])

    # 19. coupon_usages
    op.create_table(
        "coupon_usages",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("coupon_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("order_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("discount_applied", sa.Numeric(10, 2), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("coupon_id", "order_id", name="uq_coupon_usage_order"),
        sa.CheckConstraint("discount_applied >= 0", name="ck_coupon_usage_non_negative"),
    )
    op.create_index("ix_coupon_usages_coupon_id", "coupon_usages", ["coupon_id"])
    op.create_index("ix_coupon_usages_user_id", "coupon_usages", ["user_id"])
    op.create_index("ix_coupon_usages_order_id", "coupon_usages", ["order_id"])

    # 20. reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("book_id", "user_id", name="uq_review_book_user"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )
    op.create_index("ix_reviews_book_id", "reviews", ["book_id"])
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])

    # 21. inventory_movements
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("previous_stock", sa.Integer(), nullable=False),
        sa.Column("new_stock", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reference_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("performed_by", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performed_by"], ["profiles.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "movement_type IN ('entrada', 'salida', 'ajuste', 'venta', 'cancelacion')",
            name="ck_inventory_movement_type",
        ),
        sa.CheckConstraint("previous_stock >= 0", name="ck_inventory_prev_stock_non_negative"),
        sa.CheckConstraint("new_stock >= 0", name="ck_inventory_new_stock_non_negative"),
    )
    op.create_index("ix_inventory_movements_book_id", "inventory_movements", ["book_id"])
    op.create_index("ix_inventory_movements_type", "inventory_movements", ["movement_type"])
    op.create_index("ix_inventory_movements_created_at", "inventory_movements", ["created_at"])

    # 22. notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False, server_default="order"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("link", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # 23. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # Roles iniciales obligatorios
    from datetime import datetime, timezone

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        roles_table,
        [
            {
                "id": uuid4(),
                "name": "customer",
                "description": "Cliente de la librería digital BOOKLY",
                "created_at": now,
            },
            {
                "id": uuid4(),
                "name": "admin",
                "description": "Administrador del catálogo, pedidos, inventario y reportes",
                "created_at": now,
            },
        ],
    )

    # En Supabase PostgreSQL, enlazar profiles.id con auth.users(id) si existe el esquema auth
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'auth' AND table_name = 'users'
                ) THEN
                    ALTER TABLE public.profiles
                    ADD CONSTRAINT fk_profiles_auth_users
                    FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE IF EXISTS public.profiles DROP CONSTRAINT IF EXISTS fk_profiles_auth_users;")

    for table in [
        "audit_logs",
        "notifications",
        "inventory_movements",
        "reviews",
        "coupon_usages",
        "payments",
        "order_items",
        "orders",
        "coupons",
        "addresses",
        "favorites",
        "cart_items",
        "carts",
        "book_images",
        "book_categories",
        "book_authors",
        "books",
        "publishers",
        "categories",
        "authors",
        "user_roles",
        "profiles",
        "roles",
    ]:
        op.drop_table(table)
