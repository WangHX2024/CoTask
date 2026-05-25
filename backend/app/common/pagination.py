"""Pagination helpers."""
from dataclasses import dataclass

from sqlalchemy import func, select


@dataclass
class PageParams:
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (max(1, self.page) - 1) * self.size

    @property
    def limit(self) -> int:
        return max(1, min(100, self.size))


def paginate(query, params: PageParams, session):
    total = session.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()
    items = session.execute(query.offset(params.offset).limit(params.limit)).scalars().all()
    return {
        "items": items,
        "meta": {
            "page": params.page,
            "size": params.size,
            "total": int(total),
            "pages": (int(total) + params.size - 1) // params.size if params.size else 0,
        },
    }
