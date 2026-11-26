from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.exceptions.handlers import NotFoundException
from app.models.catalog import Author, Category, Publisher
from app.models.user import Profile
from app.schemas.catalog import (
    AuthorOut,
    BookOut,
    CategoryOut,
    PublisherOut,
    ReviewCreate,
    ReviewOut,
)
from app.schemas.common import PaginatedResponse
from app.services import catalog_service

router = APIRouter(tags=["Catálogo Público"])


@router.get("/books", response_model=PaginatedResponse[BookOut])
def get_books(
    search: str | None = None,
    category: str | None = None,
    author_id: UUID | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool | None = None,
    on_sale: bool | None = None,
    sort: str = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    items, meta = catalog_service.list_books(
        db,
        search=search,
        category=category,
        author_id=author_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        on_sale=on_sale,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.get("/books/featured", response_model=list[BookOut])
def get_featured_books(limit: int = Query(default=8, ge=1, le=24), db: Session = Depends(get_db)):
    items, _ = catalog_service.list_books(db, sort="rating", page=1, page_size=limit * 2)
    featured = [b for b in items if b.is_featured][:limit]
    return featured or items[:limit]


@router.get("/books/best-sellers", response_model=list[BookOut])
def get_best_sellers(limit: int = Query(default=8, ge=1, le=24), db: Session = Depends(get_db)):
    items, _ = catalog_service.list_books(db, sort="best_sellers", page=1, page_size=limit)
    return items


@router.get("/books/new-releases", response_model=list[BookOut])
def get_new_releases(limit: int = Query(default=8, ge=1, le=24), db: Session = Depends(get_db)):
    items, _ = catalog_service.list_books(db, sort="newest", page=1, page_size=limit)
    return items


@router.get("/books/{book_id}", response_model=BookOut)
def get_book_detail(book_id: str, db: Session = Depends(get_db)):
    book = catalog_service.get_book_by_id_or_slug(db, book_id)
    return catalog_service.serialize_book(book)


@router.get("/books/{book_id}/related", response_model=list[BookOut])
def get_related(book_id: str, db: Session = Depends(get_db)):
    book = catalog_service.get_book_by_id_or_slug(db, book_id)
    return catalog_service.get_related_books(db, book)


@router.get("/books/{book_id}/reviews", response_model=list[ReviewOut])
def get_reviews(book_id: str, db: Session = Depends(get_db)):
    book = catalog_service.get_book_by_id_or_slug(db, book_id)
    return catalog_service.list_book_reviews(db, book.id)


@router.post("/books/{book_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def post_review(
    book_id: str,
    payload: ReviewCreate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = catalog_service.get_book_by_id_or_slug(db, book_id)
    return catalog_service.create_or_update_review(db, book.id, current_user, payload)


@router.get("/categories", response_model=PaginatedResponse[CategoryOut])
def get_categories(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, meta = catalog_service.list_categories(db, search=search, page=page, page_size=page_size)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/categories/{category_id}", response_model=CategoryOut)
def get_category(category_id: UUID, db: Session = Depends(get_db)):
    cat = db.scalar(select(Category).where(Category.id == category_id, Category.deleted_at.is_(None)))
    if not cat:
        raise NotFoundException("Categoría no encontrada.")
    return CategoryOut(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        description=cat.description,
        icon=cat.icon,
        is_active=cat.is_active,
    )


@router.get("/authors", response_model=PaginatedResponse[AuthorOut])
def get_authors(
    search: str | None = None,
    featured: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, meta = catalog_service.list_authors(
        db, search=search, featured=featured, page=page, page_size=page_size
    )
    return PaginatedResponse(items=items, meta=meta)


@router.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: UUID, db: Session = Depends(get_db)):
    author = db.scalar(select(Author).where(Author.id == author_id, Author.deleted_at.is_(None)))
    if not author:
        raise NotFoundException("Autor no encontrado.")
    return AuthorOut(
        id=author.id,
        name=author.name,
        slug=author.slug,
        biography=author.biography,
        nationality=author.nationality,
        photo_url=author.photo_url,
        is_featured=author.is_featured,
        is_active=author.is_active,
    )


@router.get("/publishers", response_model=list[PublisherOut])
def get_publishers(db: Session = Depends(get_db)):
    pubs = db.scalars(
        select(Publisher).where(Publisher.deleted_at.is_(None), Publisher.is_active.is_(True)).order_by(Publisher.name.asc())
    ).all()
    return [PublisherOut.model_validate(p) for p in pubs]
