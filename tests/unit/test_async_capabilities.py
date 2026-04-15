from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_capabilities import AsyncCapabilitiesApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import CapabilityCreate, CapabilityUpdate


def _run(coro):
    return asyncio.run(coro)


def _capability_payload(capability_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": capability_id,
        "name": "Capability",
        "description": "Sample capability",
        "category": "environmental",
        "data_type": "numeric",
        "unit": "celsius",
        "unit_symbol": "C",
        "min_value": -40.0,
        "max_value": 125.0,
        "precision": 2,
        "icon": "thermometer",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


class _AsyncCapabilitiesHarness(AsyncCapabilitiesApiMixin):
    def __init__(self, *, create_conflict: bool = False) -> None:
        self.create_conflict = create_conflict
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/capabilities":
            if self.create_conflict:
                raise ConflictError("exists", status_code=409)
            return _capability_payload(kwargs["json"]["id"])
        if method == "GET" and path.startswith("/api/v1/capabilities/"):
            capability_id = path.rsplit("/", 1)[-1]
            return _capability_payload(capability_id)
        if method == "GET" and path == "/api/v1/capabilities":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            rows = [
                _capability_payload("cap_one"),
                _capability_payload("cap_two"),
                _capability_payload("cap_three"),
            ]
            return {"capabilities": rows[offset : offset + limit], "total": len(rows)}
        if method == "PATCH" and path.startswith("/api/v1/capabilities/"):
            capability_id = path.rsplit("/", 1)[-1]
            payload = _capability_payload(capability_id)
            payload.update(kwargs["json"])
            return payload
        if method == "DELETE" and path.startswith("/api/v1/capabilities/"):
            return None
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_capability_crud_and_ensure() -> None:
    harness = _AsyncCapabilitiesHarness()
    payload = CapabilityCreate(
        id="sdk_capability",
        name="SDK Capability",
        category="environmental",
        data_type="numeric",
        unit="celsius",
        unit_symbol="C",
        min_value=-40,
        max_value=125,
        precision=2,
        icon="thermometer",
    )

    created = _run(harness.create_capability(payload))
    assert created.id == "sdk_capability"

    fetched = _run(harness.get_capability("sdk_capability"))
    assert fetched.id == "sdk_capability"

    listed = _run(harness.list_capabilities(category="environmental", limit=10))
    assert listed.total == 3
    assert listed.capabilities[0].id == "cap_one"

    updated = _run(
        harness.update_capability(
            "sdk_capability",
            CapabilityUpdate(name="SDK Capability Updated", max_value=110),
        )
    )
    assert updated.name == "SDK Capability Updated"
    assert updated.max_value == 110

    _run(harness.delete_capability("sdk_capability"))

    ensured_created = _run(harness.ensure_capability(payload))
    assert ensured_created.id == "sdk_capability"

    conflict_harness = _AsyncCapabilitiesHarness(create_conflict=True)
    ensured_existing = _run(conflict_harness.ensure_capability(payload))
    assert ensured_existing.id == "sdk_capability"


def test_async_iter_capabilities_paginates() -> None:
    harness = _AsyncCapabilitiesHarness()

    async def collect_ids() -> list[str]:
        ids: list[str] = []
        async for capability in harness.iter_capabilities(page_size=2):
            ids.append(capability.id)
        return ids

    ids = _run(collect_ids())
    assert ids == ["cap_one", "cap_two", "cap_three"]
