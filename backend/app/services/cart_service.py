from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.exceptions.handlers import InsufficientStockException, NotFoundException
from app.models.catalog import Book, BookAuthor
from app.models.commerce import Cart, CartItem, Favorite
from app.models.user import Profile
from app.schemas.catalog import BookOut
from app.schemas.commerce import CartBookSummary, CartItemOut, CartOut
from app.services.catalog_service import _book_load_options, serialize_book


def _get_or_create_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.scalar(
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.book)
            .selectinload(Book.author_links)
            .selectinload(BookAuthor.author)
        )
        .where(Cart.user_id == user_id)
    )
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        cart = db.scalar(
            select(Cart)
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.book)
                .selectinload(Book.author_links)
                .selectinload(BookAuthor.author)
            )
            .where(Cart.user_id == user_id)
        )
    return cart


def serialize_cart(cart: Cart) -> CartOut:
    items_out: list[CartItemOut] = []
    subtotal = Decimal("0.00")
    total_count = 0

    for item in cart.items:
        book = item.book
        if not book or not book.is_active or book.deleted_at is not None:
            continue
        unit_final = book.final_price
        line_sub = (unit_final * item.quantity).quantize(Decimal("0.01"))
        subtotal += line_sub
        total_count += item.quantity
        items_out.append(
            CartItemOut(
                id=item.id,
                book_id=book.id,
                quantity=item.quantity,
                line_subtotal=line_sub,
                book=CartBookSummary(
                    id=book.id,
                    title=book.title,
                    slug=book.slug,
                    isbn=book.isbn,
                    cover_url=book.cover_url,
                    price=book.price,
                    discount_percent=book.discount_percent,
                    final_price=unit_final,
                    stock=book.stock,
                    authors=[link.author.name for link in book.author_links if link.author],
                ),
            )
        )

    return CartOut(
        id=cart.id,
        items=items_out,
        items_count=total_count,
        subtotal=subtotal.quantize(Decimal("0.01")),
    )


def get_user_cart(db: Session, user: Profile) -> CartOut:
    cart = _get_or_create_cart(db, user.id)
    return serialize_cart(cart)


def add_item_to_cart(db: Session, user: Profile, book_id: UUID, quantity: int) -> CartOut:
    book = db.scalar(
        select(Book).where(Book.id == book_id, Book.is_active.is_(True), Book.deleted_at.is_(None))
    )
    if not book:
        raise NotFoundException("Libro no disponible.")

    cart = _get_or_create_cart(db, user.id)
    existing = db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.book_id == book.id)
    )
    target_qty = (existing.quantity if existing else 0) + quantity
    if target_qty > book.stock:
        raise InsufficientStockException(
            f"Stock insuficiente para '{book.title}'. Disponible: {book.stock}."
        )

    if existing:
        existing.quantity = target_qty
    else:
        db.add(CartItem(cart_id=cart.id, book_id=book.id, quantity=quantity))
    db.commit()
    db.expire_all()
    return serialize_cart(_get_or_create_cart(db, user.id))


def update_cart_item(db: Session, user: Profile, item_id: UUID, quantity: int) -> CartOut:
    cart = _get_or_create_cart(db, user.id)
    item = db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise NotFoundException("Producto no encontrado en tu carrito.")
    book = db.scalar(select(Book).where(Book.id == item.book_id))
    if not book or quantity > book.stock:
        raise InsufficientStockException(
            f"Stock insuficiente. Disponible: {book.stock if book else 0}."
        )
    item.quantity = quantity
    db.commit()
    db.expire_all()
    return serialize_cart(_get_or_create_cart(db, user.id))


def remove_cart_item(db: Session, user: Profile, item_id: UUID) -> CartOut:
    cart = _get_or_create_cart(db, user.id)
    item = db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise NotFoundException("Producto no encontrado en tu carrito.")
    db.delete(item)
    db.commit()
    db.expire_all()
    return serialize_cart(_get_or_create_cart(db, user.id))


def clear_cart(db: Session, user: Profile) -> CartOut:
    cart = _get_or_create_cart(db, user.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.expire_all()
    return serialize_cart(_get_or_create_cart(db, user.id))


# --- Favoritos ---
def list_favorites(db: Session, user: Profile) -> list[BookOut]:
    favs = db.scalars(
        select(Favorite)
        .options(selectinload(Favorite.book).options(*_book_load_options()))
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return [
        serialize_book(f.book)
        for f in favs
        if f.book and f.book.is_active and f.book.deleted_at is None
    ]


def add_favorite(db: Session, user: Profile, book_id: UUID) -> list[BookOut]:
    book = db.scalar(
        select(Book).where(Book.id == book_id, Book.is_active.is_(True), Book.deleted_at.is_(None))
    )
    if not book:
        raise NotFoundException("Libro no encontrado.")
    exists = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.book_id == book_id)
    )
    if not exists:
        db.add(Favorite(user_id=user.id, book_id=book_id))
        db.commit()
    return list_favorites(db, user)


def remove_favorite(db: Session, user: Profile, book_id: UUID) -> list[BookOut]:
    fav = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.book_id == book_id)
    )
    if fav:
        db.delete(fav)
        db.commit()
    return list_favorites(db, user)
