from __future__ import annotations

import os
import uuid
from typing import Any

import httpx

from vfarm_device_sdk import (
    DeviceCreate,
    DeviceLocation,
    VFarmClient,
)


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _headers() -> dict[str, str]:
    return {
        "X-Farm-Key": _api_key(),
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(
        method=method,
        url=f"{_base_url()}{path}",
        headers=_headers(),
        timeout=60.0,
        **kwargs,
    )


def _ensure_farm(farm_id: str) -> None:
    payload = {
        "id": farm_id,
        "name": "SDK E2E Farm",
        "description": "Created by SDK e2e tests",
    }
    response = _request("POST", "/api/v1/farms", json=payload)
    if response.status_code not in (201, 409):
        raise AssertionError(f"Failed to ensure farm: {response.status_code} {response.text}")


def _resolve_sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


def test_sdk_device_registration_and_lookup() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-e2e-farm-{suffix}"
    device_id = f"sdk-e2e-device-{suffix}"
    _ensure_farm(farm_id)

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        result_created = client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-a", node_id="node-1", position="p1"),
                firmware_version="1.0.0",
                config={"sample_interval_seconds": 30},
            )
        )
        assert result_created.created is True
        assert result_created.device.id == device_id

        result_existing = client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-a", node_id="node-1", position="p1"),
                firmware_version="1.0.0",
            )
        )
        assert result_existing.created is False
        assert result_existing.device.id == device_id

        fetched = client.get_device(device_id)
        assert fetched.id == device_id
        assert fetched.farm_id == farm_id

        devices = client.list_devices(farm_id=farm_id, limit=50)
        ids = {d.id for d in devices.devices}
        assert device_id in ids


def test_sdk_ingest_round_trip() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-e2e-farm-{suffix}"
    device_id = f"sdk-e2e-ingest-{suffix}"
    _ensure_farm(farm_id)
    sensor_type_id = _resolve_sensor_type()

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type_id,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-b", node_id="node-2", position="p2"),
                firmware_version="1.0.0",
            )
        )

        ingest = client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type_id,
            farm_id=farm_id,
            rack_id="rack-b",
            node_id="node-2",
            firmware="1.0.0",
            temperature_value=24.6,
            humidity_value=57.3,
            uptime_s=120,
            wifi_rssi=-55,
            auto_register=False,
        )

        assert ingest.id > 0
        assert ingest.received_at is not None

        latest = _request("GET", "/api/v1/readings/latest", params={"sensor_id": device_id})
        assert latest.status_code == 200, latest.text
        body = latest.json()
        assert body["sensor_id"] == device_id
        assert body["temperature_status"] in ("ok", "error")
        assert body["humidity_status"] in ("ok", "error")


def test_sdk_register_then_ingest_single_flow() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-e2e-farm-{suffix}"
    device_id = f"sdk-e2e-flow-{suffix}"
    sensor_type_id = _resolve_sensor_type()
    _ensure_farm(farm_id)

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        registration = client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type_id,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-c", node_id="node-3", position="p3"),
                firmware_version="1.0.1",
            )
        )
        assert registration.device.id == device_id

        ingest = client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type_id,
            farm_id=farm_id,
            rack_id="rack-c",
            node_id="node-3",
            firmware="1.0.1",
            temperature_value=25.2,
            humidity_value=53.8,
            uptime_s=180,
            wifi_rssi=-52,
            auto_register=False,
        )
        assert ingest.id > 0

        latest = _request("GET", "/api/v1/readings/latest", params={"sensor_id": device_id})
        assert latest.status_code == 200, latest.text
        body = latest.json()
        assert body["sensor_id"] == device_id
        assert body["firmware"] == "1.0.1"
