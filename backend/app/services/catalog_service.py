from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.exceptions.handlers import ConflictException, NotFoundException
from app.models.catalog import (
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookImage,
    Category,
    Publisher,
)
from app.models.operations import InventoryMovement, Review
from app.models.user import Profile
from app.repositories.pagination import paginate_query
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
    ReviewCreate,
    ReviewOut,
)
from app.services.audit_service import record_audit_log
from app.utils.strings import slugify


def _book_load_options():
    return (
        selectinload(Book.publisher),
        selectinload(Book.author_links).selectinload(BookAuthor.author),
        selectinload(Book.category_links).selectinload(BookCategory.category),
        selectinload(Book.images),
    )


def serialize_book(book: Book) -> BookOut:
    authors = [
        AuthorOut(
            id=link.author.id,
            name=link.author.name,
            slug=link.author.slug,
            biography=link.author.biography,
            nationality=link.author.nationality,
            photo_url=link.author.photo_url,
            is_featured=link.author.is_featured,
            is_active=link.author.is_active,
        )
        for link in book.author_links
        if link.author and link.author.deleted_at is None
    ]
    categories = [
        CategoryOut(
            id=link.category.id,
            name=link.category.name,
            slug=link.category.slug,
            description=link.category.description,
            icon=link.category.icon,
            is_active=link.category.is_active,
        )
        for link in book.category_links
        if link.category and link.category.deleted_at is None
    ]
    return BookOut(
        id=book.id,
        title=book.title,
        slug=book.slug,
        isbn=book.isbn,
        synopsis=book.synopsis,
        price=book.price,
        discount_percent=book.discount_percent,
        final_price=book.final_price,
        stock=book.stock,
        low_stock_threshold=book.low_stock_threshold,
        pages=book.pages,
        language=book.language,
        publication_date=book.publication_date,
        cover_url=book.cover_url,
        is_featured=book.is_featured,
        is_active=book.is_active,
        sales_count=book.sales_count,
        average_rating=book.average_rating,
        reviews_count=book.reviews_count,
        publisher=book.publisher,
        authors=authors,
        categories=categories,
        images=book.images,
        created_at=book.created_at,
    )


def list_books(
    db: Session,
    *,
    search: str | None = None,
    category: str | None = None,
    author_id: UUID | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
    on_sale: bool | None = None,
    sort: str = "newest",
    include_inactive: bool = False,
    page: int = 1,
    page_size: int = 12,
):
    query = select(Book).options(*_book_load_options()).where(Book.deleted_at.is_(None))
    if not include_inactive:
        query = query.where(Book.is_active.is_(True))

    if search:
        term = f"%{search.strip()}%"
        author_book_ids = (
            select(BookAuthor.book_id)
            .join(Author, Author.id == BookAuthor.author_id)
            .where(Author.name.ilike(term))
        )
        query = query.where(
            or_(
                Book.title.ilike(term),
                Book.isbn.ilike(term),
                Book.id.in_(author_book_ids),
            )
        )

    if category:
        cat_book_ids = (
            select(BookCategory.book_id)
            .join(Category, Category.id == BookCategory.category_id)
            .where(or_(Category.slug == category, Category.name.ilike(category)))
        )
        query = query.where(Book.id.in_(cat_book_ids))

    if author_id:
        query = query.where(
            Book.id.in_(select(BookAuthor.book_id).where(BookAuthor.author_id == author_id))
        )

    if min_price is not None:
        query = query.where(Book.price >= min_price)
    if max_price is not None:
        query = query.where(Book.price <= max_price)

    if in_stock is True:
        query = query.where(Book.stock > 0)
    elif in_stock is False:
        query = query.where(Book.stock == 0)

    if on_sale:
        query = query.where(Book.discount_percent > 0)

    sort_map = {
        "newest": Book.publication_date.desc().nulls_last(),
        "price_asc": Book.price.asc(),
        "price_desc": Book.price.desc(),
        "best_sellers": Book.sales_count.desc(),
        "rating": Book.average_rating.desc(),
        "title": Book.title.asc(),
    }
    query = query.order_by(sort_map.get(sort, Book.created_at.desc()), Book.created_at.desc())

    books, meta = paginate_query(db, query, page=page, page_size=page_size)
    return [serialize_book(b) for b in books], meta


def get_book_by_id_or_slug(db: Session, identifier: str, include_inactive: bool = False) -> Book:
    query = select(Book).options(*_book_load_options()).where(Book.deleted_at.is_(None))
    if not include_inactive:
        query = query.where(Book.is_active.is_(True))
    try:
        uid = UUID(identifier)
        query = query.where(Book.id == uid)
    except ValueError:
        query = query.where(Book.slug == identifier)

    book = db.scalar(query)
    if not book:
        raise NotFoundException("Libro no encontrado.")
    return book


def get_related_books(db: Session, book: Book, limit: int = 4) -> list[BookOut]:
    cat_ids = [link.category_id for link in book.category_links]
    query = (
        select(Book)
        .options(*_book_load_options())
        .where(Book.deleted_at.is_(None), Book.is_active.is_(True), Book.id != book.id)
    )
    if cat_ids:
        query = query.where(
            Book.id.in_(
                select(BookCategory.book_id).where(BookCategory.category_id.in_(cat_ids))
            )
        )
    books = list(db.scalars(query.order_by(Book.sales_count.desc()).limit(limit)).all())
    return [serialize_book(b) for b in books]


def create_book(db: Session, payload: BookCreate, actor: Profile) -> BookOut:
    if db.scalar(select(Book).where(Book.isbn == payload.isbn)):
        raise ConflictException(f"Ya existe un libro con ISBN {payload.isbn}.")

    publisher_id = payload.publisher_id
    if not publisher_id and payload.publisher_name:
        pub = db.scalar(select(Publisher).where(Publisher.name.ilike(payload.publisher_name.strip())))
        if not pub:
            pub = Publisher(
                name=payload.publisher_name.strip(),
                slug=slugify(payload.publisher_name),
            )
            db.add(pub)
            db.flush()
        publisher_id = pub.id

    base_slug = slugify(payload.title)
    slug = f"{base_slug}-{payload.isbn[-4:]}"
    if db.scalar(select(Book).where(Book.slug == slug)):
        slug = f"{base_slug}-{payload.isbn}"

    book = Book(
        title=payload.title.strip(),
        slug=slug,
        isbn=payload.isbn.strip(),
        synopsis=payload.synopsis.strip(),
        publisher_id=publisher_id,
        price=payload.price,
        discount_percent=payload.discount_percent,
        stock=payload.stock,
        low_stock_threshold=payload.low_stock_threshold,
        pages=payload.pages,
        language=payload.language,
        publication_date=payload.publication_date,
        cover_url=payload.cover_url,
        is_featured=payload.is_featured,
        is_active=payload.is_active,
    )
    db.add(book)
    db.flush()

    for idx, author_id in enumerate(payload.author_ids, start=1):
        if not db.scalar(select(Author).where(Author.id == author_id, Author.deleted_at.is_(None))):
            raise NotFoundException(f"Autor {author_id} no encontrado.")
        db.add(BookAuthor(book_id=book.id, author_id=author_id, author_order=idx))

    for category_id in payload.category_ids:
        if not db.scalar(select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))):
            raise NotFoundException(f"Categoría {category_id} no encontrada.")
        db.add(BookCategory(book_id=book.id, category_id=category_id))

    if payload.cover_url:
        db.add(
            BookImage(
                book_id=book.id,
                image_url=payload.cover_url,
                alt_text=f"Portada de {book.title}",
                display_order=0,
                is_primary=True,
            )
        )
    for img in payload.gallery_images:
        db.add(
            BookImage(
                book_id=book.id,
                image_url=img.image_url,
                alt_text=img.alt_text,
                display_order=img.display_order,
                is_primary=img.is_primary,
            )
        )

    if payload.stock > 0:
        db.add(
            InventoryMovement(
                book_id=book.id,
                movement_type="entrada",
                quantity_delta=payload.stock,
                previous_stock=0,
                new_stock=payload.stock,
                reason="Stock inicial al crear libro",
                performed_by=actor.id,
            )
        )

    record_audit_log(
        db,
        actor_id=actor.id,
        action="BOOK_CREATED",
        entity_type="book",
        entity_id=book.id,
        new_values={"title": book.title, "isbn": book.isbn, "price": str(book.price), "stock": book.stock},
    )
    db.commit()
    return serialize_book(get_book_by_id_or_slug(db, str(book.id), include_inactive=True))


def update_book(db: Session, book_id: UUID, payload: BookUpdate, actor: Profile) -> BookOut:
    book = get_book_by_id_or_slug(db, str(book_id), include_inactive=True)
    old_snapshot = {
        "title": book.title,
        "price": str(book.price),
        "discount_percent": str(book.discount_percent),
        "stock": book.stock,
        "is_active": book.is_active,
    }

    data = payload.model_dump(exclude_unset=True)
    author_ids = data.pop("author_ids", None)
    category_ids = data.pop("category_ids", None)
    new_stock = data.pop("stock", None)

    for key, value in data.items():
        setattr(book, key, value)

    if new_stock is not None and new_stock != book.stock:
        prev = book.stock
        book.stock = new_stock
        db.add(
            InventoryMovement(
                book_id=book.id,
                movement_type="ajuste",
                quantity_delta=new_stock - prev,
                previous_stock=prev,
                new_stock=new_stock,
                reason="Ajuste desde edición de libro",
                performed_by=actor.id,
            )
        )

    if author_ids is not None:
        db.query(BookAuthor).filter(BookAuthor.book_id == book.id).delete()
        for idx, aid in enumerate(author_ids, start=1):
            db.add(BookAuthor(book_id=book.id, author_id=aid, author_order=idx))

    if category_ids is not None:
        db.query(BookCategory).filter(BookCategory.book_id == book.id).delete()
        for cid in category_ids:
            db.add(BookCategory(book_id=book.id, category_id=cid))

    record_audit_log(
        db,
        actor_id=actor.id,
        action="BOOK_UPDATED",
        entity_type="book",
        entity_id=book.id,
        old_values=old_snapshot,
        new_values={"title": book.title, "price": str(book.price), "stock": book.stock, "is_active": book.is_active},
    )
    db.commit()
    return serialize_book(get_book_by_id_or_slug(db, str(book.id), include_inactive=True))


def deactivate_book(db: Session, book_id: UUID, actor: Profile) -> None:
    book = get_book_by_id_or_slug(db, str(book_id), include_inactive=True)
    book.is_active = False
    book.deleted_at = datetime.now(timezone.utc)
    record_audit_log(
        db,
        actor_id=actor.id,
        action="BOOK_DEACTIVATED",
        entity_type="book",
        entity_id=book.id,
        old_values={"is_active": True},
        new_values={"is_active": False},
    )
    db.commit()


# --- Categorías ---
def list_categories(db: Session, *, search: str | None = None, include_inactive: bool = False, page: int = 1, page_size: int = 50):
    query = select(Category).where(Category.deleted_at.is_(None))
    if not include_inactive:
        query = query.where(Category.is_active.is_(True))
    if search:
        query = query.where(Category.name.ilike(f"%{search.strip()}%"))
    query = query.order_by(Category.name.asc())
    cats, meta = paginate_query(db, query, page=page, page_size=page_size)

    result = []
    for cat in cats:
        count = int(
            db.scalar(
                select(func.count())
                .select_from(BookCategory)
                .join(Book, Book.id == BookCategory.book_id)
                .where(BookCategory.category_id == cat.id, Book.is_active.is_(True), Book.deleted_at.is_(None))
            )
            or 0
        )
        result.append(
            CategoryOut(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                icon=cat.icon,
                is_active=cat.is_active,
                books_count=count,
            )
        )
    return result, meta


def create_category(db: Session, payload: CategoryCreate, actor: Profile) -> CategoryOut:
    slug = slugify(payload.name)
    if db.scalar(select(Category).where(or_(Category.name == payload.name.strip(), Category.slug == slug))):
        raise ConflictException("Ya existe una categoría con ese nombre.")
    cat = Category(
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        icon=payload.icon,
        is_active=payload.is_active,
    )
    db.add(cat)
    db.flush()
    record_audit_log(
        db, actor_id=actor.id, action="CATEGORY_CREATED", entity_type="category", entity_id=cat.id,
        new_values={"name": cat.name}
    )
    db.commit()
    return CategoryOut(id=cat.id, name=cat.name, slug=cat.slug, description=cat.description, icon=cat.icon, is_active=cat.is_active, books_count=0)


def update_category(db: Session, cat_id: UUID, payload: CategoryUpdate, actor: Profile) -> CategoryOut:
    cat = db.scalar(select(Category).where(Category.id == cat_id, Category.deleted_at.is_(None)))
    if not cat:
        raise NotFoundException("Categoría no encontrada.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    if payload.name:
        cat.slug = slugify(payload.name)
    record_audit_log(
        db, actor_id=actor.id, action="CATEGORY_UPDATED", entity_type="category", entity_id=cat.id,
        new_values={"name": cat.name, "is_active": cat.is_active}
    )
    db.commit()
    return CategoryOut(id=cat.id, name=cat.name, slug=cat.slug, description=cat.description, icon=cat.icon, is_active=cat.is_active, books_count=0)


def deactivate_category(db: Session, cat_id: UUID, actor: Profile) -> None:
    cat = db.scalar(select(Category).where(Category.id == cat_id, Category.deleted_at.is_(None)))
    if not cat:
        raise NotFoundException("Categoría no encontrada.")
    cat.is_active = False
    cat.deleted_at = datetime.now(timezone.utc)
    record_audit_log(db, actor_id=actor.id, action="CATEGORY_DEACTIVATED", entity_type="category", entity_id=cat.id)
    db.commit()


# --- Autores ---
def list_authors(db: Session, *, search: str | None = None, featured: bool | None = None, include_inactive: bool = False, page: int = 1, page_size: int = 50):
    query = select(Author).where(Author.deleted_at.is_(None))
    if not include_inactive:
        query = query.where(Author.is_active.is_(True))
    if featured is not None:
        query = query.where(Author.is_featured.is_(featured))
    if search:
        query = query.where(Author.name.ilike(f"%{search.strip()}%"))
    query = query.order_by(Author.name.asc())
    authors, meta = paginate_query(db, query, page=page, page_size=page_size)

    result = []
    for author in authors:
        count = int(
            db.scalar(
                select(func.count())
                .select_from(BookAuthor)
                .join(Book, Book.id == BookAuthor.book_id)
                .where(BookAuthor.author_id == author.id, Book.is_active.is_(True), Book.deleted_at.is_(None))
            )
            or 0
        )
        result.append(
            AuthorOut(
                id=author.id,
                name=author.name,
                slug=author.slug,
                biography=author.biography,
                nationality=author.nationality,
                photo_url=author.photo_url,
                is_featured=author.is_featured,
                is_active=author.is_active,
                books_count=count,
            )
        )
    return result, meta


def create_author(db: Session, payload: AuthorCreate, actor: Profile) -> AuthorOut:
    slug = slugify(payload.name)
    if db.scalar(select(Author).where(Author.slug == slug)):
        slug = f"{slug}-{str(actor.id)[:4]}"
    author = Author(**payload.model_dump(), slug=slug)
    db.add(author)
    db.flush()
    record_audit_log(db, actor_id=actor.id, action="AUTHOR_CREATED", entity_type="author", entity_id=author.id, new_values={"name": author.name})
    db.commit()
    return AuthorOut(id=author.id, name=author.name, slug=author.slug, biography=author.biography, nationality=author.nationality, photo_url=author.photo_url, is_featured=author.is_featured, is_active=author.is_active, books_count=0)


def update_author(db: Session, author_id: UUID, payload: AuthorUpdate, actor: Profile) -> AuthorOut:
    author = db.scalar(select(Author).where(Author.id == author_id, Author.deleted_at.is_(None)))
    if not author:
        raise NotFoundException("Autor no encontrado.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(author, k, v)
    if payload.name:
        author.slug = slugify(payload.name)
    record_audit_log(db, actor_id=actor.id, action="AUTHOR_UPDATED", entity_type="author", entity_id=author.id, new_values={"name": author.name})
    db.commit()
    return AuthorOut(id=author.id, name=author.name, slug=author.slug, biography=author.biography, nationality=author.nationality, photo_url=author.photo_url, is_featured=author.is_featured, is_active=author.is_active, books_count=0)


def deactivate_author(db: Session, author_id: UUID, actor: Profile) -> None:
    author = db.scalar(select(Author).where(Author.id == author_id, Author.deleted_at.is_(None)))
    if not author:
        raise NotFoundException("Autor no encontrado.")
    author.is_active = False
    author.deleted_at = datetime.now(timezone.utc)
    record_audit_log(db, actor_id=actor.id, action="AUTHOR_DEACTIVATED", entity_type="author", entity_id=author.id)
    db.commit()


# --- Reseñas ---
def list_book_reviews(db: Session, book_id: UUID) -> list[ReviewOut]:
    rows = db.scalars(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.book_id == book_id, Review.deleted_at.is_(None), Review.is_approved.is_(True))
        .order_by(Review.created_at.desc())
    ).all()
    return [
        ReviewOut(
            id=r.id,
            book_id=r.book_id,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else "Lector BOOKLY",
            rating=r.rating,
            title=r.title,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in rows
    ]


def create_or_update_review(db: Session, book_id: UUID, user: Profile, payload: ReviewCreate) -> ReviewOut:
    book = get_book_by_id_or_slug(db, str(book_id))
    review = db.scalar(
        select(Review).where(Review.book_id == book.id, Review.user_id == user.id)
    )
    if review:
        review.rating = payload.rating
        review.title = payload.title
        review.comment = payload.comment
        review.deleted_at = None
    else:
        review = Review(
            book_id=book.id,
            user_id=user.id,
            rating=payload.rating,
            title=payload.title,
            comment=payload.comment,
        )
        db.add(review)
    db.flush()

    stats = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.book_id == book.id, Review.deleted_at.is_(None), Review.is_approved.is_(True)
        )
    ).one()
    book.average_rating = Decimal(str(round(float(stats[0] or 0), 2)))
    book.reviews_count = int(stats[1] or 0)

    db.commit()
    return ReviewOut(
        id=review.id,
        book_id=review.book_id,
        user_id=review.user_id,
        user_name=user.full_name,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        created_at=review.created_at,
    )
