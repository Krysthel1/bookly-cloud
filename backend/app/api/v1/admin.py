from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_admin
from app.integrations.supabase.storage import SupabaseStorageService
from app.models.user import Profile
from app.schemas.admin import (
    AuditLogOut,
    DashboardResponse,
    InventoryBookOut,
    InventoryMovementCreate,
    InventoryMovementOut,
)
from app.schemas.catalog import (
    AuthorCreate,
    AuthorOut,
    AuthorUpdate,
    BookCreate,
    BookOut,
    BookUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
)
from app.schemas.commerce import (
    CouponCreate,
    CouponOut,
    CouponUpdate,
    OrderOut,
    OrderStatusUpdate,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import AdminUserDetailOut, AdminUserOut
from app.services import admin_service, catalog_service, order_service, user_service

router = APIRouter(prefix="/admin", tags=["Administración"])


# --- Dashboard ---
@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    start_date: date | None = None,
    end_date: date | None = None,
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_dashboard_metrics(db, start_date=start_date, end_date=end_date)


# --- Gestión de Libros ---
@router.get("/books", response_model=PaginatedResponse[BookOut])
def admin_list_books(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = catalog_service.list_books(
        db, search=search, include_inactive=True, page=page, page_size=page_size
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def admin_create_book(
    payload: BookCreate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.create_book(db, payload, admin)


@router.patch("/books/{book_id}", response_model=BookOut)
def admin_update_book(
    book_id: UUID,
    payload: BookUpdate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.update_book(db, book_id, payload, admin)


@router.delete("/books/{book_id}", response_model=MessageResponse)
def admin_delete_book(
    book_id: UUID,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    catalog_service.deactivate_book(db, book_id, admin)
    return MessageResponse(message="Libro desactivado correctamente.")


# --- Gestión de Categorías ---
@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def admin_create_category(
    payload: CategoryCreate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.create_category(db, payload, admin)


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def admin_update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.update_category(db, category_id, payload, admin)


@router.delete("/categories/{category_id}", response_model=MessageResponse)
def admin_delete_category(
    category_id: UUID,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    catalog_service.deactivate_category(db, category_id, admin)
    return MessageResponse(message="Categoría desactivada correctamente.")


# --- Gestión de Autores ---
@router.post("/authors", response_model=AuthorOut, status_code=status.HTTP_201_CREATED)
def admin_create_author(
    payload: AuthorCreate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.create_author(db, payload, admin)


@router.patch("/authors/{author_id}", response_model=AuthorOut)
def admin_update_author(
    author_id: UUID,
    payload: AuthorUpdate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return catalog_service.update_author(db, author_id, payload, admin)


@router.delete("/authors/{author_id}", response_model=MessageResponse)
def admin_delete_author(
    author_id: UUID,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    catalog_service.deactivate_author(db, author_id, admin)
    return MessageResponse(message="Autor desactivado correctamente.")


# --- Inventario ---
@router.get("/inventory", response_model=PaginatedResponse[InventoryBookOut])
def admin_inventory(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = admin_service.list_inventory(db, search=search, page=page, page_size=page_size)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/inventory/low-stock", response_model=PaginatedResponse[InventoryBookOut])
def admin_low_stock(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = admin_service.list_inventory(db, low_stock_only=True, page=page, page_size=page_size)
    return PaginatedResponse(items=items, meta=meta)


@router.post("/inventory/movements", response_model=InventoryMovementOut, status_code=status.HTTP_201_CREATED)
def admin_inventory_movement(
    payload: InventoryMovementCreate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.create_inventory_movement(db, payload, admin)


@router.get("/inventory/movements", response_model=PaginatedResponse[InventoryMovementOut])
def admin_inventory_movements(
    book_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = admin_service.list_inventory_movements(db, book_id=book_id, page=page, page_size=page_size)
    return PaginatedResponse(items=items, meta=meta)


# --- Pedidos ---
@router.get("/orders", response_model=PaginatedResponse[OrderOut])
def admin_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = order_service.admin_list_orders(
        db, status_filter=status_filter, search=search, page=page, page_size=page_size
    )
    return PaginatedResponse(items=items, meta=meta)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def admin_patch_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return order_service.admin_update_order_status(
        db, order_id, payload.status, admin, reason=payload.reason
    )


# --- Clientes ---
@router.get("/users", response_model=PaginatedResponse[AdminUserOut])
def admin_users(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = user_service.admin_list_users(
        db, search=search, is_active=is_active, page=page, page_size=page_size
    )
    return PaginatedResponse(items=items, meta=meta)


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
def admin_user_detail(
    user_id: UUID,
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.admin_get_user_detail(db, user_id)


# --- Cupones y Descuentos ---
@router.get("/coupons", response_model=list[CouponOut])
def admin_list_coupons(
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_coupons(db)


@router.post("/coupons", response_model=CouponOut, status_code=status.HTTP_201_CREATED)
def admin_create_coupon(
    payload: CouponCreate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.create_coupon(db, payload, admin)


@router.patch("/coupons/{coupon_id}", response_model=CouponOut)
def admin_update_coupon(
    coupon_id: UUID,
    payload: CouponUpdate,
    admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return admin_service.update_coupon(db, coupon_id, payload, admin)


# --- Reportes (JSON o CSV) ---
def _report_response(db: Session, report_type: str, fmt: str):
    headers, rows = admin_service.generate_report_rows(db, report_type)
    if fmt == "csv":
        csv_bytes = admin_service.export_csv_bytes(headers, rows)
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="bookly-{report_type}.csv"'},
        )
    return {"report": report_type, "count": len(rows), "rows": rows}


@router.get("/reports/sales")
def report_sales(
    format: Literal["json", "csv"] = "json",
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _report_response(db, "sales", format)


@router.get("/reports/inventory")
def report_inventory(
    format: Literal["json", "csv"] = "json",
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _report_response(db, "inventory", format)


@router.get("/reports/customers")
def report_customers(
    format: Literal["json", "csv"] = "json",
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _report_response(db, "customers", format)


@router.get("/reports/best-sellers")
def report_best_sellers(
    format: Literal["json", "csv"] = "json",
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _report_response(db, "best-sellers", format)


# --- Storage (Subida de portadas e imágenes) ---
@router.post("/storage/upload")
async def admin_upload_image(
    bucket_type: Literal["covers", "images"] = Query(default="covers"),
    file: UploadFile = File(...),
    _admin: Profile = Depends(require_admin),
):
    storage = SupabaseStorageService()
    return await storage.upload_image(file, bucket_type=bucket_type, folder="catalog")


# --- Auditoría ---
@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogOut])
def admin_audit_logs(
    entity_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _admin: Profile = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, meta = admin_service.list_audit_logs(
        db, entity_type=entity_type, page=page, page_size=page_size
    )
    return PaginatedResponse(items=items, meta=meta)
