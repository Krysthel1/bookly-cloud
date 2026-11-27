from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.exceptions.handlers import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InsufficientStockException,
    NotFoundException,
)
from app.models.catalog import Book
from app.models.commerce import (
    Address,
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    Payment,
)
from app.models.operations import InventoryMovement, Notification
from app.models.user import Profile
from app.repositories.pagination import paginate_query
from app.schemas.commerce import (
    CheckoutRequest,
    CouponValidateResponse,
    OrderOut,
)
from app.services.audit_service import record_audit_log
from app.utils.strings import generate_order_code, generate_tx_reference

SHIPPING_RATES = {
    "estandar": Decimal("12.00"),
    "express": Decimal("22.00"),
    "recojo_tienda": Decimal("0.00"),
}
FREE_STANDARD_SHIPPING_THRESHOLD = Decimal("120.00")

ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "pendiente": {"confirmado", "cancelado"},
    "confirmado": {"en_preparacion", "cancelado"},
    "en_preparacion": {"enviado", "cancelado"},
    "enviado": {"entregado"},
    "entregado": set(),
    "cancelado": set(),
}


def _ensure_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def validate_coupon(db: Session, code: str, subtotal: Decimal) -> tuple[Coupon, Decimal]:
    normalized = code.strip().upper()
    coupon = db.scalar(
        select(Coupon).where(Coupon.code == normalized, Coupon.deleted_at.is_(None))
    )
    if not coupon or not coupon.is_active:
        raise BadRequestException("El cupón ingresado no existe o no está activo.")

    now = datetime.now(timezone.utc)
    if now < _ensure_utc(coupon.starts_at) or now > _ensure_utc(coupon.expires_at):
        raise BadRequestException("El cupón se encuentra fuera de su fecha de vigencia.")

    if coupon.max_uses is not None and coupon.current_uses >= coupon.max_uses:
        raise BadRequestException("El cupón alcanzó su límite máximo de usos.")

    if subtotal < coupon.min_order_amount:
        raise BadRequestException(
            f"El monto mínimo para usar este cupón es S/ {coupon.min_order_amount:.2f}."
        )

    if coupon.discount_type == "percentage":
        discount = (subtotal * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"))
    else:
        discount = min(coupon.discount_value, subtotal).quantize(Decimal("0.01"))

    return coupon, discount


def preview_coupon(db: Session, code: str, subtotal: Decimal) -> CouponValidateResponse:
    coupon, discount = validate_coupon(db, code, subtotal)
    return CouponValidateResponse(
        valid=True,
        code=coupon.code,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        discount_amount=discount,
        message=f"Cupón {coupon.code} aplicado (-S/ {discount:.2f}).",
    )


def _compute_shipping_cost(method: str, subtotal_after_discount: Decimal) -> Decimal:
    if method == "estandar" and subtotal_after_discount >= FREE_STANDARD_SHIPPING_THRESHOLD:
        return Decimal("0.00")
    return SHIPPING_RATES[method]


def serialize_order(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_code=order.order_code,
        user_id=order.user_id,
        customer_name=order.user.full_name if order.user else None,
        customer_email=order.user.email if order.user else None,
        shipping_address_snapshot=order.shipping_address_snapshot,
        shipping_method=order.shipping_method,
        status=order.status,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        shipping_cost=order.shipping_cost,
        total=order.total,
        notes=order.notes,
        stock_restored=order.stock_restored,
        cancelled_at=order.cancelled_at,
        created_at=order.created_at,
        items=order.items,
        payment=order.payment,
    )


def _load_order(db: Session, order_id: UUID) -> Order | None:
    return db.scalar(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payment), selectinload(Order.user))
        .where(Order.id == order_id)
    )


def checkout_order(db: Session, user: Profile, payload: CheckoutRequest) -> OrderOut:
    # 1. Idempotencia: si ya existe un pedido con el mismo key del usuario, retornarlo sin duplicar
    if payload.idempotency_key:
        existing = db.scalar(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payment), selectinload(Order.user))
            .where(
                Order.idempotency_key == payload.idempotency_key,
                Order.user_id == user.id,
            )
        )
        if existing:
            return serialize_order(existing)

    # 2. Resolver dirección de envío
    address_id: UUID | None = None
    if payload.address_id:
        address = db.scalar(
            select(Address).where(
                Address.id == payload.address_id,
                Address.user_id == user.id,
                Address.deleted_at.is_(None),
            )
        )
        if not address:
            raise NotFoundException("Dirección de entrega no encontrada.")
        address_id = address.id
        address_snapshot = {
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "street_address": address.street_address,
            "district": address.district,
            "city": address.city,
            "region": address.region,
            "postal_code": address.postal_code,
            "reference": address.reference,
        }
    elif payload.shipping_address:
        address_snapshot = payload.shipping_address.model_dump()
    else:
        raise BadRequestException("Debes seleccionar o ingresar una dirección de entrega.")

    # 3. Consultar carrito persistido del usuario
    cart = db.scalar(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == user.id)
    )
    if not cart or not cart.items:
        raise BadRequestException("Tu carrito está vacío.")

    try:
        subtotal = Decimal("0.00")
        order_items_to_create: list[OrderItem] = []
        movements_to_create: list[InventoryMovement] = []

        # 4. Validación y actualización atómica de stock y precios desde BD
        for item in sorted(cart.items, key=lambda i: str(i.book_id)):
            book = db.scalar(
                select(Book).where(
                    Book.id == item.book_id,
                    Book.is_active.is_(True),
                    Book.deleted_at.is_(None),
                )
            )
            if not book:
                raise NotFoundException("Uno de los libros del carrito ya no está disponible.")

            prev_stock = book.stock
            res = db.execute(
                update(Book)
                .where(Book.id == book.id, Book.stock >= item.quantity)
                .values(
                    stock=Book.stock - item.quantity,
                    sales_count=Book.sales_count + item.quantity,
                )
            )
            if res.rowcount != 1:
                raise InsufficientStockException(
                    f"Stock insuficiente para '{book.title}'. Disponible: {prev_stock}."
                )

            final_unit = book.final_price
            line_total = (final_unit * item.quantity).quantize(Decimal("0.01"))
            subtotal += line_total

            order_items_to_create.append(
                OrderItem(
                    book_id=book.id,
                    book_title_snapshot=book.title,
                    book_isbn_snapshot=book.isbn,
                    unit_price=book.price,
                    discount_percent_snapshot=book.discount_percent,
                    final_unit_price=final_unit,
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )
            movements_to_create.append(
                InventoryMovement(
                    book_id=book.id,
                    movement_type="venta",
                    quantity_delta=-item.quantity,
                    previous_stock=prev_stock,
                    new_stock=prev_stock - item.quantity,
                    reason="Venta confirmada por checkout",
                    performed_by=user.id,
                )
            )

        # 5. Descuento por cupón en backend
        discount_amount = Decimal("0.00")
        coupon_obj: Coupon | None = None
        if payload.coupon_code:
            coupon_obj, discount_amount = validate_coupon(db, payload.coupon_code, subtotal)
            coupon_res = db.execute(
                update(Coupon)
                .where(
                    Coupon.id == coupon_obj.id,
                    (Coupon.max_uses.is_(None)) | (Coupon.current_uses < Coupon.max_uses),
                )
                .values(current_uses=Coupon.current_uses + 1)
            )
            if coupon_res.rowcount != 1:
                raise ConflictException("El cupón alcanzó su límite máximo de usos.")

        net_subtotal = max(Decimal("0.00"), subtotal - discount_amount)
        shipping_cost = _compute_shipping_cost(payload.shipping_method, net_subtotal)
        total = (net_subtotal + shipping_cost).quantize(Decimal("0.01"))

        is_instant_payment = payload.payment_method in ("tarjeta", "yape", "plin")
        initial_order_status = "confirmado" if is_instant_payment else "pendiente"
        payment_status = "simulado_aprobado" if is_instant_payment else "pendiente"
        now = datetime.now(timezone.utc)

        order = Order(
            order_code=generate_order_code(),
            idempotency_key=payload.idempotency_key,
            user_id=user.id,
            address_id=address_id,
            shipping_address_snapshot=address_snapshot,
            shipping_method=payload.shipping_method,
            status=initial_order_status,
            subtotal=subtotal.quantize(Decimal("0.01")),
            discount_amount=discount_amount,
            shipping_cost=shipping_cost,
            total=total,
            coupon_id=coupon_obj.id if coupon_obj else None,
            notes=payload.notes,
        )
        db.add(order)
        db.flush()

        for oi in order_items_to_create:
            oi.order_id = order.id
            db.add(oi)

        for mv in movements_to_create:
            mv.reference_id = order.id
            db.add(mv)

        db.add(
            Payment(
                order_id=order.id,
                method=payload.payment_method,
                status=payment_status,
                amount=total,
                transaction_reference=generate_tx_reference(payload.payment_method[:3].upper()),
                is_simulated=True,
                paid_at=now if is_instant_payment else None,
            )
        )

        if coupon_obj:
            db.add(
                CouponUsage(
                    coupon_id=coupon_obj.id,
                    user_id=user.id,
                    order_id=order.id,
                    discount_applied=discount_amount,
                )
            )

        # Vaciar carrito
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

        # Notificación para el cliente
        db.add(
            Notification(
                user_id=user.id,
                title=f"Pedido {order.order_code} registrado",
                message=f"Tu pedido por S/ {total:.2f} se encuentra en estado '{initial_order_status}'.",
                type="order",
                link=f"/mi-cuenta/pedidos/{order.id}",
            )
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    created = _load_order(db, order.id)
    return serialize_order(created)


def list_user_orders(db: Session, user: Profile, page: int = 1, page_size: int = 10):
    query = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payment), selectinload(Order.user))
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    orders, meta = paginate_query(db, query, page=page, page_size=page_size)
    return [serialize_order(o) for o in orders], meta


def get_user_order(db: Session, user: Profile, order_id: UUID) -> OrderOut:
    order = _load_order(db, order_id)
    if not order:
        raise NotFoundException("Pedido no encontrado.")
    if order.user_id != user.id and "admin" not in user.role_names:
        raise ForbiddenException("No tienes permiso para consultar este pedido.")
    return serialize_order(order)


def _restore_order_stock_once(db: Session, order: Order, actor_id: UUID, reason: str) -> None:
    res = db.execute(
        update(Order)
        .where(Order.id == order.id, Order.stock_restored.is_(False))
        .values(stock_restored=True)
    )
    if res.rowcount != 1:
        return

    for item in order.items:
        book = db.scalar(select(Book).where(Book.id == item.book_id))
        if not book:
            continue
        prev_stock = book.stock
        new_stock = prev_stock + item.quantity
        book.stock = new_stock
        book.sales_count = max(0, book.sales_count - item.quantity)
        db.add(
            InventoryMovement(
                book_id=book.id,
                movement_type="cancelacion",
                quantity_delta=item.quantity,
                previous_stock=prev_stock,
                new_stock=new_stock,
                reason=reason,
                reference_id=order.id,
                performed_by=actor_id,
            )
        )


def cancel_user_order(db: Session, user: Profile, order_id: UUID) -> OrderOut:
    order = _load_order(db, order_id)
    if not order:
        raise NotFoundException("Pedido no encontrado.")
    if order.user_id != user.id:
        raise ForbiddenException("No tienes permiso para cancelar este pedido.")
    if order.status not in ("pendiente", "confirmado"):
        raise BadRequestException(
            f"No se puede cancelar un pedido en estado '{order.status}'."
        )

    order.status = "cancelado"
    order.cancelled_at = datetime.now(timezone.utc)
    if order.payment and order.payment.status == "simulado_aprobado":
        order.payment.status = "reembolsado"

    _restore_order_stock_once(
        db, order, user.id, f"Devolución por cancelación del pedido {order.order_code}"
    )

    db.add(
        Notification(
            user_id=user.id,
            title=f"Pedido {order.order_code} cancelado",
            message="Tu pedido fue cancelado y el inventario fue restaurado.",
            type="order",
            link=f"/mi-cuenta/pedidos/{order.id}",
        )
    )
    db.commit()
    return serialize_order(_load_order(db, order.id))


def admin_list_orders(
    db: Session,
    *,
    status_filter: str | None = None,
    search: str | None = None,
    user_id: UUID | None = None,
    page: int = 1,
    page_size: int = 15,
):
    query = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payment), selectinload(Order.user))
        .order_by(Order.created_at.desc())
    )
    if user_id:
        query = query.where(Order.user_id == user_id)
    if status_filter:
        query = query.where(Order.status == status_filter)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(Order.order_code.ilike(term))
    orders, meta = paginate_query(db, query, page=page, page_size=page_size)
    return [serialize_order(o) for o in orders], meta


def admin_update_order_status(
    db: Session, order_id: UUID, new_status: str, admin: Profile, reason: str | None = None
) -> OrderOut:
    order = _load_order(db, order_id)
    if not order:
        raise NotFoundException("Pedido no encontrado.")

    allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise BadRequestException(
            f"Transición no permitida de '{order.status}' a '{new_status}'."
        )

    old_status = order.status
    order.status = new_status

    if new_status == "cancelado":
        order.cancelled_at = datetime.now(timezone.utc)
        if order.payment and order.payment.status == "simulado_aprobado":
            order.payment.status = "reembolsado"
        _restore_order_stock_once(
            db,
            order,
            admin.id,
            reason or f"Cancelación administrativa de {order.order_code}",
        )
    elif new_status == "entregado" and order.payment and order.payment.status == "pendiente":
        order.payment.status = "simulado_aprobado"
        order.payment.paid_at = datetime.now(timezone.utc)

    db.add(
        Notification(
            user_id=order.user_id,
            title=f"Actualización de pedido {order.order_code}",
            message=f"Tu pedido pasó al estado '{new_status}'.",
            type="order",
            link=f"/mi-cuenta/pedidos/{order.id}",
        )
    )
    record_audit_log(
        db,
        actor_id=admin.id,
        action="ORDER_STATUS_UPDATED",
        entity_type="order",
        entity_id=order.id,
        old_values={"status": old_status},
        new_values={"status": new_status, "reason": reason},
    )
    db.commit()
    return serialize_order(_load_order(db, order.id))
