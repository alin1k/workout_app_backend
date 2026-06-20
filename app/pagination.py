"""Reusable limit/offset pagination for list endpoints.

`parse_pagination` reads the query string into a validated `Pagination`,
raising `ValidationError` (rendered as 400 by the global error handler) on
bad input. `paginated_response` wraps serialized items in the standard
`{"data": [...], "pagination": {...}}` envelope.
"""

from dataclasses import dataclass

from app.services.errors import ValidationError

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass
class Pagination:
    limit: int
    offset: int


def _parse_int(args, key: str, default: int) -> int:
    raw = args.get(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"{key} must be an integer", field=key) from exc


def parse_pagination(
    args, *, default_limit: int = DEFAULT_LIMIT, max_limit: int = MAX_LIMIT
) -> Pagination:
    limit = _parse_int(args, "limit", default_limit)
    offset = _parse_int(args, "offset", 0)

    if limit < 1:
        raise ValidationError("limit must be >= 1", field="limit")
    if limit > max_limit:
        raise ValidationError(f"limit must be <= {max_limit}", field="limit")
    if offset < 0:
        raise ValidationError("offset must be >= 0", field="offset")

    return Pagination(limit=limit, offset=offset)


def paginated_response(items: list, total: int, pagination: Pagination) -> dict:
    count = len(items)
    return {
        "data": items,
        "pagination": {
            "limit": pagination.limit,
            "offset": pagination.offset,
            "count": count,
            "total": total,
            "has_next": pagination.offset + count < total,
            "has_prev": pagination.offset > 0,
        },
    }
