from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vfarm_device_sdk.core import VFarmAsyncApiClient
from vfarm_device_sdk.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    VFarmApiError,
)


def _run(coro):
    return asyncio.run(coro)


def test_async_request_success_and_204() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/ok"):
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)

    result = _run(sdk._request("GET", "/ok"))
    assert result == {"ok": True}

    no_content = _run(sdk._request("DELETE", "/gone"))
    assert no_content is None

    _run(client.aclose())


@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (401, AuthenticationError),
        (404, NotFoundError),
        (409, ConflictError),
        (400, ValidationError),
        (422, ValidationError),
        (500, VFarmApiError),
    ],
)
def test_async_request_error_mapping(status: int, exc_type: type[Exception]) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=json.dumps({"detail": "boom"}))

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)

    with pytest.raises(exc_type):
        _run(sdk._request("GET", "/err"))

    _run(client.aclose())
