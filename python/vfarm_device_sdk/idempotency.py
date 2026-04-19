from __future__ import annotations

import re
from uuid import uuid4


def generate_idempotency_key(prefix: str | None = None) -> str:
    """
    Generate an idempotency key with optional normalized prefix.

    Parameters
    ----------
    prefix:
        Optional key prefix.

    Returns
    -------
    str
        Generated idempotency key.

    Examples
    --------
    .. code-block:: python

       key = generate_idempotency_key("ingest")
       print(key)

    Common Errors
    -------------
    - ``N/A`` -> ``None``: Pure helper; no API request.
    """
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
    """
    Return headers merged with optional ``Idempotency-Key``.

    Parameters
    ----------
    headers:
        Existing headers or ``None``.
    idempotency_key:
        Optional idempotency key.

    Returns
    -------
    dict[str, str] | None
        Merged headers or ``None`` if no inputs.

    Examples
    --------
    .. code-block:: python

       headers = with_idempotency_header(headers={"X-Test": "1"}, idempotency_key="abc")
       print(headers["Idempotency-Key"])

    Common Errors
    -------------
    - ``N/A`` -> ``None``: Pure helper; no API request.
    """
    if not idempotency_key:
        return dict(headers) if headers else None
    merged = dict(headers or {})
    merged["Idempotency-Key"] = idempotency_key
    return merged


def _normalize_prefix(prefix: str | None) -> str:
    """
    Normalize idempotency prefix to lowercase slug format.

    Parameters
    ----------
    prefix:
        Optional raw prefix string.

    Returns
    -------
    str
        Normalized prefix or empty string.

    Examples
    --------
    .. code-block:: python

       print(_normalize_prefix("Ingest Job"))

    Common Errors
    -------------
    - ``N/A`` -> ``None``: Pure helper; no API request.
    """
    if not prefix:
        return ""
    cleaned = re.sub(r"[^a-z0-9]+", "-", prefix.strip().lower())
    return cleaned.strip("-")
