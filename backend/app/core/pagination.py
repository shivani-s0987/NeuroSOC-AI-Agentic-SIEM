from typing import Literal

from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    sort_by: str = Query(default="id"),
    sort_order: Literal["asc", "desc"] = "desc",
):
    return {"page": page, "page_size": page_size, "sort_by": sort_by, "sort_order": sort_order}


def paginated(items: list, page: int, page_size: int, total: int) -> dict:
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": max(1, (total + page_size - 1) // page_size),
        },
    }


def apply_sort(query, model, sort_by: str, allowed: set[str], sort_order: str, default: str = "id"):
    field_name = sort_by if sort_by in allowed else default
    field = getattr(model, field_name)
    ordered = field.asc() if sort_order == "asc" else field.desc()
    return query.order_by(ordered, model.id.asc() if sort_order == "asc" else model.id.desc())
