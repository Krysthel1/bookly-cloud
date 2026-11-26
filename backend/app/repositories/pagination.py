import math
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.schemas.common import PaginationMeta


def paginate_query(db: Session, query: Select, page: int = 1, page_size: int = 12) -> tuple[list, PaginationMeta]:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = int(db.scalar(count_query) or 0)
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all())
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
    return items, meta
