from functools import lru_cache
from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada de BOOKLY cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BOOKLY"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./bookly_dev.db"
    direct_database_url: str | None = None
    db_pool_mode: Literal["auto", "transaction", "queue"] = "auto"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"

    supabase_bucket_covers: str = "book-covers"
    supabase_bucket_images: str = "book-images"
    supabase_bucket_avatars: str = "avatars"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_default: str = "120/minute"
    log_level: str = "INFO"

    @field_validator("database_url", "direct_database_url", mode="before")
    @classmethod
    def normalize_postgres_scheme(cls, value: str | None) -> str | None:
        if not value:
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_transaction_pooler(self) -> bool:
        if self.db_pool_mode == "transaction":
            return True
        if self.db_pool_mode == "queue":
            return False
        return ":6543" in self.database_url or "pooler.supabase.com" in self.database_url

    @property
    def supabase_jwks_url(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json" if base else ""

    @property
    def supabase_issuer(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1" if base else ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
