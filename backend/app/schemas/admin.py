from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InventoryMovementCreate(BaseModel):
    book_id: UUID
    movement_type: Literal["entrada", "salida", "ajuste"]
    quantity: int = Field(ge=0, description="Para entrada/salida es cantidad (>0). Para ajuste es el nuevo stock objetivo.")
    reason: str = Field(min_length=3, max_length=500)


class InventoryMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    book_id: UUID
    book_title: str | None = None
    movement_type: str
    quantity_delta: int
    previous_stock: int
    new_stock: int
    reason: str
    reference_id: UUID | None = None
    performed_by: UUID | None = None
    performer_name: str | None = None
    created_at: datetime


class InventoryBookOut(BaseModel):
    id: UUID
    title: str
    isbn: str
    stock: int
    low_stock_threshold: int
    price: Decimal
    is_active: bool
    status_label: str


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None = None
    actor_email: str | None = None
    action: str
    entity_type: str
    entity_id: str
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime


class DashboardKpis(BaseModel):
    total_revenue: Decimal
    today_sales: Decimal
    month_sales: Decimal
    orders_count: int
    customers_count: int
    books_count: int
    low_stock_count: int
    average_ticket: Decimal
    sales_variation_percent: float


class DashboardSeriesPoint(BaseModel):
    label: str
    value: float
    count: int = 0


class DashboardResponse(BaseModel):
    kpis: DashboardKpis
    sales_evolution: list[DashboardSeriesPoint]
    monthly_revenue: list[DashboardSeriesPoint]
    sales_by_category: list[DashboardSeriesPoint]
    top_selling_books: list[DashboardSeriesPoint]
    orders_by_status: list[DashboardSeriesPoint]
    new_customers: list[DashboardSeriesPoint]
