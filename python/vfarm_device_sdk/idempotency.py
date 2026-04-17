from __future__ import annotations

import re
from uuid import uuid4


def generate_idempotency_key(prefix: str | None = None) -> str:
    token = uuid4().hex
    normalized = _normalize_prefix(prefix)
    if not normalized:
        return token
    return f"{normalized}-{token}"


def with_idempotency_header(
    *,
    headers: dict[str, str] | None,
    idempotency_key: str | None,
) -> dict[str, str] | None:
    if not idempotency_key:
        return dict(headers) if headers else None
    merged = dict(headers or {})
    merged["Idempotency-Key"] = idempotency_key
    return merged


def _normalize_prefix(prefix: str | None) -> str:
    if not prefix:
        return ""
    cleaned = re.sub(r"[^a-z0-9]+", "-", prefix.strip().lower())
    return cleaned.strip("-")
