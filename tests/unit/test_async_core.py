from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vfarm_device_sdk.core import RetryPolicy, VFarmAsyncApiClient
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


def test_async_retries_safe_method_status_codes_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"detail": "try again"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, b: b)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)
    result = _run(sdk._request("GET", "/retry"))

    assert result == {"ok": True}
    assert calls == 2
    assert sleeps == [0.2]
    _run(client.aclose())


def test_async_does_not_retry_unsafe_method_by_default() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, json={"detail": "boom"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)

    with pytest.raises(VFarmApiError):
        _run(sdk._request("POST", "/retry"))

    assert calls == 1
    _run(client.aclose())


def test_async_retries_unsafe_method_when_globally_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def fake_sleep(_delay: float) -> None:
        return None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"detail": "retry me"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    policy = RetryPolicy(allow_unsafe_retries=True)
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", retry_policy=policy, client=client)
    result = _run(sdk._request("PATCH", "/retry"))

    assert result == {"ok": True}
    assert calls == 2
    _run(client.aclose())


def test_async_retries_unsafe_method_with_per_call_override(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def fake_sleep(_delay: float) -> None:
        return None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"detail": "retry me"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)
    result = _run(sdk._request("POST", "/retry", retry=True))

    assert result == {"ok": True}
    assert calls == 2
    _run(client.aclose())


def test_async_per_call_retry_false_suppresses_safe_method_retry() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"detail": "first"})
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)

    with pytest.raises(VFarmApiError):
        _run(sdk._request("GET", "/retry", retry=False))

    assert calls == 1
    _run(client.aclose())


def test_async_honors_retry_after_header_for_429(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "1.5"}, json={"detail": "slow down"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.0)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)
    result = _run(sdk._request("GET", "/retry"))

    assert result == {"ok": True}
    assert sleeps == [1.5]
    _run(client.aclose())


def test_async_uses_jitter_when_retry_after_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, json={"detail": "slow down"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.123)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)
    result = _run(sdk._request("GET", "/retry"))

    assert result == {"ok": True}
    assert sleeps == [0.123]
    _run(client.aclose())


def test_async_retries_timeout_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("timed out", request=request)
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.05)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", client=client)
    result = _run(sdk._request("GET", "/retry"))

    assert result == {"ok": True}
    assert calls == 2
    assert sleeps == [0.05]
    _run(client.aclose())


def test_async_stops_after_max_retries_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def fake_sleep(_delay: float) -> None:
        return None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, json={"detail": "boom"})

    monkeypatch.setattr("vfarm_device_sdk.core.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("vfarm_device_sdk.core.asyncio.sleep", fake_sleep)

    policy = RetryPolicy(max_retries=2)
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    sdk = VFarmAsyncApiClient("http://test.local", "k", retry_policy=policy, client=client)

    with pytest.raises(VFarmApiError) as exc:
        _run(sdk._request("GET", "/retry"))

    assert calls == 3
    assert exc.value.status_code == 500
    _run(client.aclose())
