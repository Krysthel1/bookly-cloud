from datetime import datetime, timedelta, timezone
import os
import sys
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["APP_ENV"] = "test"
os.environ["SUPABASE_JWT_SECRET"] = "test-super-secret-jwt-key-for-bookly-pytest"
os.environ["SUPABASE_URL"] = "https://testproject.supabase.co"
os.environ["SUPABASE_JWT_AUDIENCE"] = "authenticated"

from app.config.settings import get_settings

get_settings.cache_clear()

from app.database.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.catalog import Author, Book, BookAuthor, BookCategory, Category, Publisher  # noqa: E402
from app.models.commerce import Coupon  # noqa: E402
from app.models.user import Profile, Role, UserRole  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(conn, _rec):
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSessionLocal()

    # Seed mínimo para pruebas
    customer_role = Role(id=uuid4(), name="customer", description="Cliente")
    admin_role = Role(id=uuid4(), name="admin", description="Administrador")
    session.add_all([customer_role, admin_role])

    customer_id = UUID("11111111-1111-1111-1111-111111111111")
    other_customer_id = UUID("22222222-2222-2222-2222-222222222222")
    admin_id = UUID("99999999-9999-9999-9999-999999999999")

    customer = Profile(id=customer_id, email="cliente@bookly.pe", full_name="Cliente Uno", is_active=True)
    other_customer = Profile(id=other_customer_id, email="otro@bookly.pe", full_name="Cliente Dos", is_active=True)
    admin = Profile(id=admin_id, email="admin@bookly.pe", full_name="Admin BOOKLY", is_active=True)
    session.add_all([customer, other_customer, admin])
    session.flush()

    session.add_all([
        UserRole(user_id=customer_id, role_id=customer_role.id),
        UserRole(user_id=other_customer_id, role_id=customer_role.id),
        UserRole(user_id=admin_id, role_id=customer_role.id),
        UserRole(user_id=admin_id, role_id=admin_role.id),
    ])

    cat = Category(id=uuid4(), name="Literatura", slug="literatura", description="Narrativa")
    author = Author(id=uuid4(), name="Julio Ramón Ribeyro", slug="julio-ramon-ribeyro", nationality="Peruana")
    pub = Publisher(id=uuid4(), name="Seix Barral", slug="seix-barral")
    session.add_all([cat, author, pub])
    session.flush()

    book1 = Book(
        id=uuid4(),
        title="La palabra del mudo",
        slug="la-palabra-del-mudo",
        isbn="9789972409332",
        synopsis="Cuentos completos de Julio Ramón Ribeyro en edición especial.",
        publisher_id=pub.id,
        price=100.00,
        discount_percent=10.00,  # final_price = 90.00
        stock=5,
        low_stock_threshold=2,
        pages=800,
        language="Español",
        is_featured=True,
        is_active=True,
    )
    book2 = Book(
        id=uuid4(),
        title="Los heraldos negros",
        slug="los-heraldos-negros",
        isbn="9788437607115",
        synopsis="Poemario fundacional de César Vallejo.",
        publisher_id=pub.id,
        price=50.00,
        discount_percent=0.00,
        stock=2,
        low_stock_threshold=2,
        pages=160,
        language="Español",
        is_featured=False,
        is_active=True,
    )
    session.add_all([book1, book2])
    session.flush()
    session.add_all([
        BookAuthor(book_id=book1.id, author_id=author.id),
        BookAuthor(book_id=book2.id, author_id=author.id),
        BookCategory(book_id=book1.id, category_id=cat.id),
        BookCategory(book_id=book2.id, category_id=cat.id),
    ])

    now = datetime.now(timezone.utc)
    session.add(
        Coupon(
            id=uuid4(),
            code="BOOKLY10",
            description="10% off",
            discount_type="percentage",
            discount_value=10.00,
            min_order_amount=50.00,
            max_uses=10,
            current_uses=0,
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
    )
    session.commit()

    try:
        yield session, {"customer": customer_id, "other": other_customer_id, "admin": admin_id, "book1": book1.id, "book2": book2.id, "cat": cat.id, "author": author.id}
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    session, ids = db_session

    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc, ids, session
    app.dependency_overrides.clear()


def make_token(user_id: UUID, email: str = "user@bookly.pe") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "iss": "https://testproject.supabase.co/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
