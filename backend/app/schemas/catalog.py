from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AuthorBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    biography: str | None = None
    nationality: str | None = Field(default=None, max_length=80)
    photo_url: str | None = None
    is_featured: bool = False
    is_active: bool = True


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    biography: str | None = None
    nationality: str | None = Field(default=None, max_length=80)
    photo_url: str | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    biography: str | None = None
    nationality: str | None = None
    photo_url: str | None = None
    is_featured: bool
    is_active: bool
    books_count: int = 0


class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=60)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=60)
    is_active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    is_active: bool
    books_count: int = 0


class PublisherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    country: str | None = None
    website: str | None = None


class BookImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    image_url: str
    alt_text: str | None = None
    display_order: int
    is_primary: bool


class BookImageCreate(BaseModel):
    image_url: str
    alt_text: str | None = None
    display_order: int = 0
    is_primary: bool = False


class BookCreate(BaseModel):
    title: str = Field(min_length=2, max_length=250)
    isbn: str = Field(min_length=8, max_length=32)
    synopsis: str = Field(min_length=10)
    publisher_id: UUID | None = None
    publisher_name: str | None = None
    price: Decimal = Field(ge=0)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    stock: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    pages: int | None = Field(default=None, gt=0)
    language: str = Field(default="Español", max_length=60)
    publication_date: date | None = None
    cover_url: str | None = None
    is_featured: bool = False
    is_active: bool = True
    author_ids: list[UUID] = Field(min_length=1)
    category_ids: list[UUID] = Field(min_length=1)
    gallery_images: list[BookImageCreate] = Field(default_factory=list)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=250)
    isbn: str | None = Field(default=None, min_length=8, max_length=32)
    synopsis: str | None = Field(default=None, min_length=10)
    publisher_id: UUID | None = None
    price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    stock: int | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)
    pages: int | None = Field(default=None, gt=0)
    language: str | None = Field(default=None, max_length=60)
    publication_date: date | None = None
    cover_url: str | None = None
    is_featured: bool | None = None
    is_active: bool | None = None
    author_ids: list[UUID] | None = None
    category_ids: list[UUID] | None = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    isbn: str
    synopsis: str
    price: Decimal
    discount_percent: Decimal
    final_price: Decimal
    stock: int
    low_stock_threshold: int
    pages: int | None = None
    language: str
    publication_date: date | None = None
    cover_url: str | None = None
    is_featured: bool
    is_active: bool
    sales_count: int
    average_rating: Decimal
    reviews_count: int
    publisher: PublisherOut | None = None
    authors: list[AuthorOut] = Field(default_factory=list)
    categories: list[CategoryOut] = Field(default_factory=list)
    images: list[BookImageOut] = Field(default_factory=list)
    created_at: datetime


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=150)
    comment: str = Field(min_length=5, max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    book_id: UUID
    user_id: UUID
    user_name: str
    rating: int
    title: str | None = None
    comment: str
    created_at: datetime
