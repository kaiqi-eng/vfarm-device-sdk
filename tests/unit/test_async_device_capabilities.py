from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_device_capabilities import AsyncDeviceCapabilitiesApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import DeviceCapabilityCreate


def _run(coro):
    return asyncio.run(coro)


class _AsyncDeviceCapabilitiesHarness(AsyncDeviceCapabilitiesApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.create_conflict = False

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()

        if method == "GET" and path.endswith("/capabilities"):
            return {
                "device_id": "dev-1",
                "sensor_type_id": "dht22",
                "capabilities": [
                    {
                        "device_id": "dev-1",
                        "capability_id": "temperature",
                        "capability_name": "Temperature",
                        "category": "environmental",
                        "data_type": "numeric",
                        "unit": "celsius",
                        "unit_symbol": "C",
                        "source": "sensor_type",
                        "base_min_value": -40.0,
                        "base_max_value": 125.0,
                        "calibration_offset": 0.0,
                        "calibration_scale": 1.0,
                        "custom_min": None,
                        "custom_max": None,
                        "effective_min": -40.0,
                        "effective_max": 125.0,
                        "enabled": True,
                        "last_calibrated_at": None,
                        "notes": None,
                    }
                ],
                "total": 1,
            }

        if method == "POST" and path.endswith("/capabilities"):
            if self.create_conflict:
                raise ConflictError("exists", status_code=409)
            body = kwargs["json"]
            return {
                "device_id": "dev-1",
                "capability_id": body["capability_id"],
                "capability_name": "Temperature",
                "category": "environmental",
                "data_type": "numeric",
                "unit": "celsius",
                "unit_symbol": "C",
                "source": "device_override",
                "base_min_value": -40.0,
                "base_max_value": 125.0,
                "calibration_offset": body.get("calibration_offset", 0.0),
                "calibration_scale": body.get("calibration_scale", 1.0),
                "custom_min": body.get("custom_min"),
                "custom_max": body.get("custom_max"),
                "effective_min": body.get("custom_min", -40.0),
                "effective_max": body.get("custom_max", 125.0),
                "enabled": body.get("enabled", True),
                "last_calibrated_at": None,
                "notes": body.get("notes"),
                "created_at": now,
                "updated_at": now,
            }

        if method == "PATCH" and "/capabilities/" in path:
            body = kwargs["json"]
            cap_id = path.rsplit("/", 1)[-1]
            return {
                "device_id": "dev-1",
                "capability_id": cap_id,
                "capability_name": "Temperature",
                "category": "environmental",
                "data_type": "numeric",
                "unit": "celsius",
                "unit_symbol": "C",
                "source": "device_override",
                "base_min_value": -40.0,
                "base_max_value": 125.0,
                "calibration_offset": body.get("calibration_offset", 0.0),
                "calibration_scale": body.get("calibration_scale", 1.0),
                "custom_min": body.get("custom_min"),
                "custom_max": body.get("custom_max"),
                "effective_min": body.get("custom_min", -40.0),
                "effective_max": body.get("custom_max", 125.0),
                "enabled": body.get("enabled", True),
                "last_calibrated_at": None,
                "notes": body.get("notes"),
                "created_at": now,
                "updated_at": now,
            }

        if method == "DELETE" and "/capabilities/" in path:
            return None

        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_device_capabilities_crud() -> None:
    sdk = _AsyncDeviceCapabilitiesHarness()
    listed = _run(sdk.list_device_capabilities("dev-1"))
    assert listed.device_id == "dev-1"
    assert listed.total == 1

    created = _run(
        sdk.create_device_capability_override(
            "dev-1",
            DeviceCapabilityCreate(
                capability_id="temperature",
                calibration_offset=0.4,
                calibration_scale=1.01,
                custom_min=-5.0,
                custom_max=45.0,
                enabled=True,
                notes="create",
            ),
        )
    )
    assert created.source == "device_override"
    assert created.calibration_offset == 0.4

    _run(sdk.delete_device_capability_override("dev-1", "temperature"))


def test_async_upsert_and_calibrate_helpers() -> None:
    sdk = _AsyncDeviceCapabilitiesHarness()
    created = _run(
        sdk.upsert_device_capability_override(
            "dev-1",
            capability_id="temperature",
            calibration_offset=0.2,
            calibration_scale=1.0,
            notes="upsert-create",
        )
    )
    assert created.calibration_offset == 0.2

    sdk.create_conflict = True
    updated = _run(
        sdk.upsert_device_capability_override(
            "dev-1",
            capability_id="temperature",
            calibration_offset=0.1,
            calibration_scale=0.99,
            notes="upsert-update",
        )
    )
    assert updated.calibration_offset == 0.1
    assert updated.calibration_scale == 0.99

    calibrated = _run(
        sdk.calibrate_device_capability(
            "dev-1",
            "temperature",
            offset=0.05,
            scale=1.0,
            notes="calibrate",
        )
    )
    assert calibrated.calibration_offset == 0.05
