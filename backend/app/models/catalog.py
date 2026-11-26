from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.operations import InventoryMovement, Review


class Author(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    book_links: Mapped[list["BookAuthor"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    book_links: Mapped[list["BookCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Publisher(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "publishers"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="publisher")


class Book(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_books_price_non_negative"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_books_discount_range",
        ),
        CheckConstraint("stock >= 0", name="ck_books_stock_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="ck_books_low_stock_non_negative"),
        CheckConstraint("pages IS NULL OR pages > 0", name="ck_books_pages_positive"),
        CheckConstraint("sales_count >= 0", name="ck_books_sales_count_non_negative"),
        Index("ix_books_active_featured", "is_active", "is_featured"),
    )

    title: Mapped[str] = mapped_column(String(250), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(280), unique=True, nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    synopsis: Mapped[str] = mapped_column(Text, nullable=False)
    publisher_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("publishers.id", ondelete="SET NULL"), nullable=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(60), default="Español", nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sales_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("0.00"), nullable=False
    )
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    publisher: Mapped["Publisher | None"] = relationship(back_populates="books")
    author_links: Mapped[list["BookAuthor"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="BookAuthor.author_order"
    )
    category_links: Mapped[list["BookCategory"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    images: Mapped[list["BookImage"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="BookImage.display_order"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )

    @property
    def final_price(self) -> Decimal:
        price_dec = Decimal(str(self.price))
        discount_dec = Decimal(str(self.discount_percent or 0))
        if discount_dec > 0:
            discounted = price_dec * (Decimal("100") - discount_dec) / Decimal("100")
            return discounted.quantize(Decimal("0.01"))
        return price_dec.quantize(Decimal("0.01"))


class BookAuthor(Base):
    __tablename__ = "book_authors"

    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True
    )
    author_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    book: Mapped["Book"] = relationship(back_populates="author_links")
    author: Mapped["Author"] = relationship(back_populates="book_links")


class BookCategory(Base):
    __tablename__ = "book_categories"

    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )

    book: Mapped["Book"] = relationship(back_populates="category_links")
    category: Mapped["Category"] = relationship(back_populates="book_links")


class BookImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "book_images"

    book_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    book: Mapped["Book"] = relationship(back_populates="images")
