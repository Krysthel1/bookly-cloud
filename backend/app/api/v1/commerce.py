from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import Profile
from app.schemas.catalog import BookOut
from app.schemas.commerce import (
    CartItemCreate,
    CartItemUpdate,
    CartOut,
    CheckoutRequest,
    CouponValidateRequest,
    CouponValidateResponse,
    FavoriteCreate,
    OrderOut,
)
from app.schemas.common import PaginatedResponse
from app.services import cart_service, order_service

router = APIRouter(tags=["Carrito, Favoritos y Pedidos"])


# --- Carrito ---
@router.get("/cart", response_model=CartOut)
def get_cart(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_service.get_user_cart(db, current_user)


@router.post("/cart/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    payload: CartItemCreate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.add_item_to_cart(db, current_user, payload.book_id, payload.quantity)


@router.patch("/cart/items/{item_id}", response_model=CartOut)
def patch_cart_item(
    item_id: UUID,
    payload: CartItemUpdate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.update_cart_item(db, current_user, item_id, payload.quantity)


@router.delete("/cart/items/{item_id}", response_model=CartOut)
def delete_cart_item(
    item_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.remove_cart_item(db, current_user, item_id)


@router.delete("/cart", response_model=CartOut)
def empty_cart(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_service.clear_cart(db, current_user)


# --- Favoritos ---
@router.get("/favorites", response_model=list[BookOut])
def get_favorites(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_service.list_favorites(db, current_user)


@router.post("/favorites", response_model=list[BookOut], status_code=status.HTTP_201_CREATED)
def post_favorite(
    payload: FavoriteCreate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.add_favorite(db, current_user, payload.book_id)


@router.delete("/favorites/{book_id}", response_model=list[BookOut])
def delete_favorite(
    book_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.remove_favorite(db, current_user, book_id)


# --- Cupones ---
@router.post("/coupons/validate", response_model=CouponValidateResponse)
def validate_coupon_endpoint(
    payload: CouponValidateRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.preview_coupon(db, payload.code, payload.subtotal)


# --- Pedidos y Checkout ---
@router.post("/orders/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.checkout_order(db, current_user, payload)


@router.get("/orders", response_model=PaginatedResponse[OrderOut])
def get_my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, meta = order_service.list_user_orders(db, current_user, page=page, page_size=page_size)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_my_order_detail(
    order_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.get_user_order(db, current_user, order_id)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_my_order(
    order_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.cancel_user_order(db, current_user, order_id)
