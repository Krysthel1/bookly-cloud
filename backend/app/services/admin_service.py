import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.exceptions.handlers import BadRequestException, ConflictException, NotFoundException
from app.models.catalog import Book, BookCategory, Category
from app.models.commerce import Coupon, Order, OrderItem
from app.models.operations import AuditLog, InventoryMovement
from app.models.user import Profile
from app.repositories.pagination import paginate_query
from app.schemas.admin import (
    AuditLogOut,
    DashboardKpis,
    DashboardResponse,
    DashboardSeriesPoint,
    InventoryBookOut,
    InventoryMovementCreate,
    InventoryMovementOut,
)
from app.schemas.commerce import CouponCreate, CouponOut, CouponUpdate
from app.services.audit_service import record_audit_log


# --- Inventario ---
def list_inventory(db: Session, *, low_stock_only: bool = False, search: str | None = None, page: int = 1, page_size: int = 20):
    query = select(Book).where(Book.deleted_at.is_(None)).order_by(Book.stock.asc(), Book.title.asc())
    if low_stock_only:
        query = query.where(Book.stock <= Book.low_stock_threshold)
    if search:
        term = f"%{search.strip()}%"
        query = query.where((Book.title.ilike(term)) | (Book.isbn.ilike(term)))

    books, meta = paginate_query(db, query, page=page, page_size=page_size)
    items = []
    for b in books:
        if b.stock == 0:
            label = "Agotado"
        elif b.stock <= b.low_stock_threshold:
            label = "Stock bajo"
        else:
            label = "Disponible"
        items.append(
            InventoryBookOut(
                id=b.id,
                title=b.title,
                isbn=b.isbn,
                stock=b.stock,
                low_stock_threshold=b.low_stock_threshold,
                price=b.price,
                is_active=b.is_active,
                status_label=label,
            )
        )
    return items, meta


def create_inventory_movement(db: Session, payload: InventoryMovementCreate, admin: Profile) -> InventoryMovementOut:
    book = db.scalar(select(Book).where(Book.id == payload.book_id, Book.deleted_at.is_(None)))
    if not book:
        raise NotFoundException("Libro no encontrado.")

    prev_stock = book.stock
    if payload.movement_type == "entrada":
        if payload.quantity <= 0:
            raise BadRequestException("La cantidad de entrada debe ser mayor a 0.")
        new_stock = prev_stock + payload.quantity
    elif payload.movement_type == "salida":
        if payload.quantity <= 0:
            raise BadRequestException("La cantidad de salida debe ser mayor a 0.")
        if payload.quantity > prev_stock:
            raise BadRequestException(f"No se puede retirar más del stock actual ({prev_stock}).")
        new_stock = prev_stock - payload.quantity
    else:  # ajuste
        if payload.quantity < 0:
            raise BadRequestException("El stock ajustado no puede ser negativo.")
        new_stock = payload.quantity

    delta = new_stock - prev_stock
    book.stock = new_stock

    movement = InventoryMovement(
        book_id=book.id,
        movement_type=payload.movement_type,
        quantity_delta=delta,
        previous_stock=prev_stock,
        new_stock=new_stock,
        reason=payload.reason,
        performed_by=admin.id,
    )
    db.add(movement)
    record_audit_log(
        db,
        actor_id=admin.id,
        action="INVENTORY_MOVEMENT",
        entity_type="book",
        entity_id=book.id,
        old_values={"stock": prev_stock},
        new_values={"stock": new_stock, "type": payload.movement_type, "reason": payload.reason},
    )
    db.commit()
    db.refresh(movement)
    return InventoryMovementOut(
        id=movement.id,
        book_id=book.id,
        book_title=book.title,
        movement_type=movement.movement_type,
        quantity_delta=movement.quantity_delta,
        previous_stock=movement.previous_stock,
        new_stock=movement.new_stock,
        reason=movement.reason,
        reference_id=movement.reference_id,
        performed_by=admin.id,
        performer_name=admin.full_name,
        created_at=movement.created_at,
    )


def list_inventory_movements(db: Session, *, book_id: UUID | None = None, page: int = 1, page_size: int = 20):
    query = (
        select(InventoryMovement)
        .options(selectinload(InventoryMovement.book), selectinload(InventoryMovement.performer))
        .order_by(InventoryMovement.created_at.desc())
    )
    if book_id:
        query = query.where(InventoryMovement.book_id == book_id)
    rows, meta = paginate_query(db, query, page=page, page_size=page_size)
    return [
        InventoryMovementOut(
            id=m.id,
            book_id=m.book_id,
            book_title=m.book.title if m.book else None,
            movement_type=m.movement_type,
            quantity_delta=m.quantity_delta,
            previous_stock=m.previous_stock,
            new_stock=m.new_stock,
            reason=m.reason,
            reference_id=m.reference_id,
            performed_by=m.performed_by,
            performer_name=m.performer.full_name if m.performer else "Sistema",
            created_at=m.created_at,
        )
        for m in rows
    ], meta


# --- Cupones ---
def list_coupons(db: Session) -> list[CouponOut]:
    rows = db.scalars(
        select(Coupon).where(Coupon.deleted_at.is_(None)).order_by(Coupon.created_at.desc())
    ).all()
    return [CouponOut.model_validate(c) for c in rows]


def create_coupon(db: Session, payload: CouponCreate, admin: Profile) -> CouponOut:
    code = payload.code.strip().upper()
    if db.scalar(select(Coupon).where(Coupon.code == code)):
        raise ConflictException(f"El cupón {code} ya existe.")
    if payload.expires_at <= payload.starts_at:
        raise BadRequestException("La fecha de expiración debe ser posterior al inicio.")
    if payload.discount_type == "percentage" and payload.discount_value > 100:
        raise BadRequestException("El descuento porcentual no puede superar el 100%.")

    coupon = Coupon(
        code=code,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_order_amount=payload.min_order_amount,
        max_uses=payload.max_uses,
        starts_at=payload.starts_at,
        expires_at=payload.expires_at,
        is_active=payload.is_active,
    )
    db.add(coupon)
    db.flush()
    record_audit_log(
        db, actor_id=admin.id, action="COUPON_CREATED", entity_type="coupon", entity_id=coupon.id,
        new_values={"code": code, "discount_value": str(coupon.discount_value)}
    )
    db.commit()
    return CouponOut.model_validate(coupon)


def update_coupon(db: Session, coupon_id: UUID, payload: CouponUpdate, admin: Profile) -> CouponOut:
    coupon = db.scalar(select(Coupon).where(Coupon.id == coupon_id, Coupon.deleted_at.is_(None)))
    if not coupon:
        raise NotFoundException("Cupón no encontrado.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(coupon, k, v)
    record_audit_log(
        db, actor_id=admin.id, action="COUPON_UPDATED", entity_type="coupon", entity_id=coupon.id,
        new_values={"is_active": coupon.is_active}
    )
    db.commit()
    return CouponOut.model_validate(coupon)


# --- Dashboard y Reportes ---
def get_dashboard_metrics(
    db: Session, *, start_date: date | None = None, end_date: date | None = None
) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    orders_query = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.asc())
    if start_date:
        orders_query = orders_query.where(
            Order.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        )
    if end_date:
        orders_query = orders_query.where(
            Order.created_at <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        )

    all_orders = list(db.scalars(orders_query).all())
    valid_orders = [o for o in all_orders if o.status != "cancelado"]

    total_revenue = sum((o.total for o in valid_orders), Decimal("0.00"))
    today_sales = sum(
        (o.total for o in valid_orders if o.created_at.replace(tzinfo=timezone.utc) >= today_start),
        Decimal("0.00"),
    )
    month_sales = sum(
        (o.total for o in valid_orders if o.created_at.replace(tzinfo=timezone.utc) >= month_start),
        Decimal("0.00"),
    )
    prev_month_sales = sum(
        (
            o.total
            for o in valid_orders
            if prev_month_start <= o.created_at.replace(tzinfo=timezone.utc) < month_start
        ),
        Decimal("0.00"),
    )
    if prev_month_sales > 0:
        variation = float(((month_sales - prev_month_sales) / prev_month_sales) * Decimal("100"))
    else:
        variation = 100.0 if month_sales > 0 else 0.0

    avg_ticket = (
        (total_revenue / len(valid_orders)).quantize(Decimal("0.01"))
        if valid_orders
        else Decimal("0.00")
    )

    customers_count = int(
        db.scalar(select(func.count(Profile.id)).where(Profile.deleted_at.is_(None))) or 0
    )
    books_count = int(
        db.scalar(select(func.count(Book.id)).where(Book.deleted_at.is_(None), Book.is_active.is_(True)))
        or 0
    )
    low_stock_count = int(
        db.scalar(
            select(func.count(Book.id)).where(
                Book.deleted_at.is_(None),
                Book.is_active.is_(True),
                Book.stock <= Book.low_stock_threshold,
            )
        )
        or 0
    )

    # Series
    daily_totals: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
    monthly_totals: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
    status_counts: dict[str, int] = defaultdict(int)

    for o in all_orders:
        status_counts[o.status] += 1
        if o.status == "cancelado":
            continue
        day_key = o.created_at.strftime("%Y-%m-%d")
        d_val, d_cnt = daily_totals[day_key]
        daily_totals[day_key] = (round(d_val + float(o.total), 2), d_cnt + 1)

        month_key = o.created_at.strftime("%Y-%m")
        m_val, m_cnt = monthly_totals[month_key]
        monthly_totals[month_key] = (round(m_val + float(o.total), 2), m_cnt + 1)

    sales_evolution = [
        DashboardSeriesPoint(label=k, value=v[0], count=v[1])
        for k, v in sorted(daily_totals.items())[-14:]
    ]
    monthly_revenue = [
        DashboardSeriesPoint(label=k, value=v[0], count=v[1])
        for k, v in sorted(monthly_totals.items())[-12:]
    ]
    orders_by_status = [
        DashboardSeriesPoint(label=k, value=float(v), count=v) for k, v in status_counts.items()
    ]

    # Ventas por categoría
    cat_sales_rows = db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(OrderItem.line_total), 0),
            func.coalesce(func.sum(OrderItem.quantity), 0),
        )
        .join(BookCategory, BookCategory.category_id == Category.id)
        .join(OrderItem, OrderItem.book_id == BookCategory.book_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "cancelado")
        .group_by(Category.name)
    ).all()
    sales_by_category = [
        DashboardSeriesPoint(label=row[0], value=float(row[1]), count=int(row[2]))
        for row in cat_sales_rows
    ]

    # Top libros vendidos
    top_books = db.scalars(
        select(Book)
        .where(Book.deleted_at.is_(None), Book.is_active.is_(True))
        .order_by(Book.sales_count.desc())
        .limit(8)
    ).all()
    top_selling_books = [
        DashboardSeriesPoint(
            label=b.title[:26] + ("..." if len(b.title) > 26 else ""),
            value=float(b.sales_count),
            count=b.sales_count,
        )
        for b in top_books
    ]

    # Nuevos clientes por día
    profiles = db.scalars(select(Profile).where(Profile.deleted_at.is_(None))).all()
    cust_by_day: dict[str, int] = defaultdict(int)
    for p in profiles:
        cust_by_day[p.created_at.strftime("%Y-%m-%d")] += 1
    new_customers = [
        DashboardSeriesPoint(label=k, value=float(v), count=v)
        for k, v in sorted(cust_by_day.items())[-14:]
    ]

    return DashboardResponse(
        kpis=DashboardKpis(
            total_revenue=total_revenue.quantize(Decimal("0.01")),
            today_sales=today_sales.quantize(Decimal("0.01")),
            month_sales=month_sales.quantize(Decimal("0.01")),
            orders_count=len(all_orders),
            customers_count=customers_count,
            books_count=books_count,
            low_stock_count=low_stock_count,
            average_ticket=avg_ticket,
            sales_variation_percent=round(variation, 2),
        ),
        sales_evolution=sales_evolution,
        monthly_revenue=monthly_revenue,
        sales_by_category=sales_by_category,
        top_selling_books=top_selling_books,
        orders_by_status=orders_by_status,
        new_customers=new_customers,
    )


def generate_report_rows(
    db: Session,
    report_type: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[str], list[dict]]:
    if report_type == "sales":
        query = (
            select(Order)
            .options(selectinload(Order.user), selectinload(Order.payment))
            .order_by(Order.created_at.desc())
        )
        if start_date:
            query = query.where(
                Order.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            )
        if end_date:
            query = query.where(
                Order.created_at <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
            )
        orders = db.scalars(query).all()
        headers = ["order_code", "fecha", "cliente", "estado", "metodo_pago", "subtotal", "descuento", "envio", "total"]
        rows = [
            {
                "order_code": o.order_code,
                "fecha": o.created_at.isoformat(),
                "cliente": o.user.email if o.user else "",
                "estado": o.status,
                "metodo_pago": o.payment.method if o.payment else "",
                "subtotal": str(o.subtotal),
                "descuento": str(o.discount_amount),
                "envio": str(o.shipping_cost),
                "total": str(o.total),
            }
            for o in orders
        ]
        return headers, rows

    if report_type == "inventory":
        books = db.scalars(select(Book).where(Book.deleted_at.is_(None)).order_by(Book.stock.asc())).all()
        headers = ["isbn", "titulo", "precio_pen", "descuento_pct", "stock", "umbral_alerta", "activo"]
        rows = [
            {
                "isbn": b.isbn,
                "titulo": b.title,
                "precio_pen": str(b.price),
                "descuento_pct": str(b.discount_percent),
                "stock": b.stock,
                "umbral_alerta": b.low_stock_threshold,
                "activo": b.is_active,
            }
            for b in books
        ]
        return headers, rows

    if report_type == "customers":
        cust_query = select(Profile).where(Profile.deleted_at.is_(None)).order_by(Profile.created_at.desc())
        if start_date:
            cust_query = cust_query.where(
                Profile.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            )
        if end_date:
            cust_query = cust_query.where(
                Profile.created_at <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
            )
        users = db.scalars(cust_query).all()
        headers = ["id", "nombre", "email", "telefono", "activo", "fecha_registro"]
        rows = [
            {
                "id": str(u.id),
                "nombre": u.full_name,
                "email": u.email,
                "telefono": u.phone or "",
                "activo": u.is_active,
                "fecha_registro": u.created_at.isoformat(),
            }
            for u in users
        ]
        return headers, rows

    if report_type == "best-sellers":
        books = db.scalars(
            select(Book).where(Book.deleted_at.is_(None)).order_by(Book.sales_count.desc()).limit(50)
        ).all()
        headers = ["isbn", "titulo", "ventas_totales", "precio_final_pen", "calificacion", "stock_actual"]
        rows = [
            {
                "isbn": b.isbn,
                "titulo": b.title,
                "ventas_totales": b.sales_count,
                "precio_final_pen": str(b.final_price),
                "calificacion": str(b.average_rating),
                "stock_actual": b.stock,
            }
            for b in books
        ]
        return headers, rows

    raise BadRequestException("Tipo de reporte inválido.")


def export_csv_bytes(headers: list[str], rows: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


def list_audit_logs(db: Session, *, entity_type: str | None = None, page: int = 1, page_size: int = 25):
    query = (
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
    )
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    rows, meta = paginate_query(db, query, page=page, page_size=page_size)
    return [
        AuditLogOut(
            id=r.id,
            actor_id=r.actor_id,
            actor_email=r.actor.email if r.actor else "Sistema",
            action=r.action,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            old_values=r.old_values,
            new_values=r.new_values,
            ip_address=r.ip_address,
            created_at=r.created_at,
        )
        for r in rows
    ], meta
