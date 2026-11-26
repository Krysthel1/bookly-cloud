from collections.abc import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.config.settings import get_settings


class Base(DeclarativeBase):
    """Clase base declarativa de SQLAlchemy 2.0 para todos los modelos BOOKLY."""


def create_db_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url

    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    connect_args: dict = {
        "connect_timeout": 10,
        "application_name": settings.app_name,
    }

    if "sslmode=" not in url and "localhost" not in url and "127.0.0.1" not in url:
        connect_args["sslmode"] = "require"

    if settings.is_transaction_pooler:
        # Supavisor en modo transacción ya gestiona el pool en servidor y no admite sentencias preparadas persistentes
        connect_args["prepare_threshold"] = None
        return create_engine(
            url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee una sesión transaccional por solicitud."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
