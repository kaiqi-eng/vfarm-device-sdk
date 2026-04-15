from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_sensor_types import AsyncSensorTypeApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import SensorTypeCreate, SensorTypeUpdate


def _run(coro):
    return asyncio.run(coro)


def _sensor_type_payload(sensor_type_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": sensor_type_id,
        "name": "DHT22",
        "manufacturer": "Acme",
        "description": "Temp/humidity sensor",
        "datasheet_url": None,
        "communication": "digital",
        "power_voltage": "3.3V",
        "capabilities": [],
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


class _AsyncSensorTypeHarness(AsyncSensorTypeApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.create_conflict = False

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "GET" and path == "/api/v1/sensor-types":
            return {"sensor_types": [_sensor_type_payload("dht22")], "total": 1}
        if method == "GET" and path.startswith("/api/v1/sensor-types/"):
            sensor_type_id = path.rsplit("/", 1)[-1]
            return _sensor_type_payload(sensor_type_id)
        if method == "POST" and path == "/api/v1/sensor-types":
            if self.create_conflict:
                raise ConflictError("duplicate", status_code=409)
            return _sensor_type_payload(kwargs["json"]["id"])
        if method == "PATCH" and path.startswith("/api/v1/sensor-types/"):
            sensor_type_id = path.rsplit("/", 1)[-1]
            payload = _sensor_type_payload(sensor_type_id)
            payload.update(kwargs["json"])
            return payload
        if method == "DELETE":
            return None
        raise AssertionError(f"Unhandled call {method} {path}")


def test_async_sensor_type_crud_and_list() -> None:
    sdk = _AsyncSensorTypeHarness()

    listed = _run(sdk.list_sensor_types(manufacturer="Acme", limit=50))
    assert listed.total == 1
    assert listed.sensor_types[0].id == "dht22"

    created = _run(
        sdk.create_sensor_type(
            SensorTypeCreate(
                id="st_1",
                name="Sensor One",
                manufacturer="Acme",
                communication="digital",
            )
        )
    )
    assert created.id == "st_1"

    fetched = _run(sdk.get_sensor_type("st_1"))
    assert fetched.id == "st_1"

    updated = _run(
        sdk.update_sensor_type(
            "st_1",
            SensorTypeUpdate(
                name="Sensor One Updated",
                description="updated",
            ),
        )
    )
    assert updated.name == "Sensor One Updated"
    assert updated.description == "updated"

    _run(sdk.remove_sensor_type_capability("st_1", "temperature"))
    _run(sdk.delete_sensor_type("st_1"))


def test_async_ensure_sensor_type_created_and_existing() -> None:
    sdk = _AsyncSensorTypeHarness()
    payload = SensorTypeCreate(
        id="st_ensure",
        name="Sensor Ensure",
        manufacturer="Acme",
    )

    created = _run(sdk.ensure_sensor_type(payload))
    assert created.id == "st_ensure"

    sdk.create_conflict = True
    existing = _run(sdk.ensure_sensor_type(payload))
    assert existing.id == "st_ensure"
