from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_devices import AsyncDeviceApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import DeviceCreate, DeviceLocation


def _run(coro):
    return asyncio.run(coro)


def _device_payload(device_id: str, farm_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": device_id,
        "device_type": "sensor",
        "farm_id": farm_id,
        "status": "online",
        "created_at": now,
        "updated_at": now,
    }


class _AsyncDeviceHarness(AsyncDeviceApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.register_conflict = False

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/devices":
            if self.register_conflict:
                raise ConflictError("duplicate", status_code=409)
            return {"id": kwargs["json"]["id"], "created_at": datetime.now(timezone.utc).isoformat()}
        if method == "GET" and path.startswith("/api/v1/devices/"):
            device_id = path.rsplit("/", 1)[-1]
            return _device_payload(device_id, "farm-a")
        if method == "GET" and path == "/api/v1/devices":
            return {
                "devices": [_device_payload("d-1", "farm-a")],
                "total": 1,
                "online_count": 1,
                "offline_count": 0,
                "registered_count": 1,
                "maintenance_count": 0,
                "error_count": 0,
                "unhealthy_count": 0,
            }
        raise AssertionError(f"Unhandled call {method} {path}")


def test_async_device_register_and_get() -> None:
    sdk = _AsyncDeviceHarness()
    created = _run(
        sdk.register_device(
            DeviceCreate(
                id="dev-1",
                farm_id="farm-a",
                device_type="sensor",
                device_model="DHT22",
                location=DeviceLocation(rack_id="r1", node_id="n1", position="p1"),
            )
        )
    )
    assert created.id == "dev-1"

    fetched = _run(sdk.get_device("dev-1"))
    assert fetched.id == "dev-1"
    assert fetched.farm_id == "farm-a"


def test_async_ensure_device_created_and_existing() -> None:
    sdk = _AsyncDeviceHarness()
    payload = DeviceCreate(
        id="dev-ensure",
        farm_id="farm-a",
        device_type="sensor",
        device_model="DHT22",
    )

    created = _run(sdk.ensure_device(payload))
    assert created.created is True
    assert created.device.id == "dev-ensure"
    assert created.created_response is not None

    sdk.register_conflict = True
    existing = _run(sdk.ensure_device(payload))
    assert existing.created is False
    assert existing.device.id == "dev-ensure"
    assert existing.created_response is None


def test_async_list_devices() -> None:
    sdk = _AsyncDeviceHarness()
    listed = _run(sdk.list_devices(farm_id="farm-a", limit=50))
    assert listed.total == 1
    assert listed.devices[0].id == "d-1"
