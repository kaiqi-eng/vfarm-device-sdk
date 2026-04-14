from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

import httpx

from vfarm_device_sdk import AsyncVFarmClient, DeviceCreate, DeviceLocation


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
        "name": "SDK Async Readings E2E Farm",
        "description": "Created by async readings e2e tests",
    }
    response = _request("POST", "/api/v1/farms", json=payload)
    if response.status_code not in (201, 409):
        raise AssertionError(f"Failed to ensure farm: {response.status_code} {response.text}")


def _resolve_sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


async def _resolve_sensor_type_for_ingest(client: AsyncVFarmClient) -> str:
    preferred = _resolve_sensor_type()
    try:
        sensor_type = await client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        capabilities = {c["capability_id"] for c in sensor_type.get("capabilities", [])}
        if {"temperature", "humidity"}.issubset(capabilities):
            return preferred
    except Exception:
        pass

    listing = await client._request(
        "GET",
        "/api/v1/sensor-types",
        params={"limit": 200, "offset": 0},
        timeout=60.0,
    )
    for sensor_type in listing.get("sensor_types", []):
        capabilities = {c["capability_id"] for c in sensor_type.get("capabilities", [])}
        if {"temperature", "humidity"}.issubset(capabilities):
            return sensor_type["id"]

    raise RuntimeError("No sensor type with both temperature and humidity capabilities was found for async readings E2E")


def test_sdk_async_readings_round_trip() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-readings-farm-{suffix}"
        device_id = f"sdk-async-readings-dev-{suffix}"
        _ensure_farm(farm_id)

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            sensor_type = await _resolve_sensor_type_for_ingest(client)
            await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id=sensor_type,
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-r", node_id="node-r", position="pr"),
                    firmware_version="1.0.0",
                )
            )

            await client.ingest_reading(
                sensor_id=device_id,
                sensor_type=sensor_type,
                farm_id=farm_id,
                rack_id="rack-r",
                node_id="node-r",
                firmware="1.0.0",
                temperature_value=22.9,
                humidity_value=55.2,
                uptime_s=100,
                wifi_rssi=-48,
                auto_register=False,
            )

            latest = await client.get_latest_reading(device_id)
            assert latest.sensor_id == device_id

            readings = await client.list_readings(device_id, limit=20)
            assert readings.sensor_id == device_id
            assert readings.count >= 1

            stats = await client.get_reading_stats(device_id, window="1h")
            assert stats.sensor_id == device_id
            assert stats.total_readings >= 1

            analytics = await client.get_readings_analytics(device_id, window="1h", recent_limit=20)
            assert analytics.sensor_id == device_id
            assert analytics.latest is not None
            assert analytics.recent.count >= 1
            assert analytics.stats.total_readings >= 1

    asyncio.run(_test())
