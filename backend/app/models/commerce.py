from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.catalog import Book
    from app.models.user import Profile


class Cart(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "carts"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    user: Mapped["Profile"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.created_at"
    )


class CartItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
    )

    cart_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    book: Mapped["Book"] = relationship()


class Favorite(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_favorite_user_book"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    user: Mapped["Profile"] = relationship(back_populates="favorites")
    book: Mapped["Book"] = relationship()


class Address(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "addresses"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(60), default="Casa", nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    street_address: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["Profile"] = relationship(back_populates="addresses")


class Coupon(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint("discount_type IN ('percentage', 'fixed')", name="ck_coupons_type"),
        CheckConstraint("discount_value > 0", name="ck_coupons_value_positive"),
        CheckConstraint("min_order_amount >= 0", name="ck_coupons_min_order_non_negative"),
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_coupons_max_uses_positive"),
        CheckConstraint("current_uses >= 0", name="ck_coupons_current_uses_non_negative"),
    )

    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendiente', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado')",
            name="ck_orders_status",
        ),
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="ck_orders_discount_non_negative"),
        CheckConstraint("shipping_cost >= 0", name="ck_orders_shipping_non_negative"),
        CheckConstraint("total >= 0", name="ck_orders_total_non_negative"),
    )

    order_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    address_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True
    )
    shipping_address_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    shipping_method: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pendiente", nullable=False, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    coupon_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock_restored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["Profile"] = relationship(back_populates="orders")
    coupon: Mapped["Coupon | None"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class OrderItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("final_unit_price >= 0", name="ck_order_items_final_price_non_negative"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )

    order_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    book_title_snapshot: Mapped[str] = mapped_column(String(250), nullable=False)
    book_isbn_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_percent_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    final_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    order: Mapped["Order"] = relationship(back_populates="items")
    book: Mapped["Book"] = relationship()


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('tarjeta', 'yape', 'plin', 'contra_entrega')",
            name="ck_payments_method",
        ),
        CheckConstraint(
            "status IN ('pendiente', 'simulado_aprobado', 'fallido', 'reembolsado')",
            name="ck_payments_status",
        ),
        CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
    )

    order_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="payment")


class CouponUsage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "coupon_usages"
    __table_args__ = (
        UniqueConstraint("coupon_id", "order_id", name="uq_coupon_usage_order"),
        CheckConstraint("discount_applied >= 0", name="ck_coupon_usage_non_negative"),
    )

    coupon_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discount_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
