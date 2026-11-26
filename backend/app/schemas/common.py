from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None
