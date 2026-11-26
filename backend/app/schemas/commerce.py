from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    book_id: UUID
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartBookSummary(BaseModel):
    id: UUID
    title: str
    slug: str
    isbn: str
    cover_url: str | None = None
    price: Decimal
    discount_percent: Decimal
    final_price: Decimal
    stock: int
    authors: list[str] = Field(default_factory=list)


class CartItemOut(BaseModel):
    id: UUID
    book_id: UUID
    quantity: int
    line_subtotal: Decimal
    book: CartBookSummary


class CartOut(BaseModel):
    id: UUID
    items: list[CartItemOut]
    items_count: int
    subtotal: Decimal


class FavoriteCreate(BaseModel):
    book_id: UUID


class CouponValidateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    subtotal: Decimal = Field(ge=0)


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: str
    discount_value: Decimal
    discount_amount: Decimal
    message: str


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    description: str | None = None
    discount_type: Literal["percentage", "fixed"]
    discount_value: Decimal = Field(gt=0)
    min_order_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_uses: int | None = Field(default=None, gt=0)
    starts_at: datetime
    expires_at: datetime
    is_active: bool = True


class CouponUpdate(BaseModel):
    description: str | None = None
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: Decimal | None = Field(default=None, gt=0)
    min_order_amount: Decimal | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    min_order_amount: Decimal
    max_uses: int | None = None
    current_uses: int
    starts_at: datetime
    expires_at: datetime
    is_active: bool


class CheckoutShippingAddress(BaseModel):
    recipient_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)
    street_address: str = Field(min_length=4, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    region: str = Field(min_length=2, max_length=100)
    postal_code: str | None = None
    reference: str | None = None


class CheckoutRequest(BaseModel):
    address_id: UUID | None = None
    shipping_address: CheckoutShippingAddress | None = None
    shipping_method: Literal["estandar", "express", "recojo_tienda"] = "estandar"
    payment_method: Literal["tarjeta", "yape", "plin", "contra_entrega"] = "tarjeta"
    coupon_code: str | None = None
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=100)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    book_id: UUID
    book_title_snapshot: str
    book_isbn_snapshot: str
    unit_price: Decimal
    discount_percent_snapshot: Decimal
    final_unit_price: Decimal
    quantity: int
    line_total: Decimal


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    method: str
    status: str
    amount: Decimal
    transaction_reference: str
    is_simulated: bool
    paid_at: datetime | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_code: str
    user_id: UUID
    customer_name: str | None = None
    customer_email: str | None = None
    shipping_address_snapshot: dict
    shipping_method: str
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total: Decimal
    notes: str | None = None
    stock_restored: bool
    cancelled_at: datetime | None = None
    created_at: datetime
    items: list[OrderItemOut] = Field(default_factory=list)
    payment: PaymentOut | None = None


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "pendiente", "confirmado", "en_preparacion", "enviado", "entregado", "cancelado"
    ]
    reason: str | None = None
