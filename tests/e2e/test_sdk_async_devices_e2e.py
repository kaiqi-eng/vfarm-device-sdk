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
        "name": "SDK Async E2E Farm",
        "description": "Created by async SDK e2e tests",
    }
    response = _request("POST", "/api/v1/farms", json=payload)
    if response.status_code not in (201, 409):
        raise AssertionError(f"Failed to ensure farm: {response.status_code} {response.text}")


def test_sdk_async_device_registration_and_lookup() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-farm-{suffix}"
        device_id = f"sdk-async-device-{suffix}"
        _ensure_farm(farm_id)

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            created = await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-a", node_id="node-1", position="p1"),
                    firmware_version="1.0.0",
                )
            )
            assert created.device.id == device_id

            fetched = await client.get_device(device_id)
            assert fetched.id == device_id
            assert fetched.farm_id == farm_id

            listed = await client.list_devices(farm_id=farm_id, limit=20)
            assert any(d.id == device_id for d in listed.devices)

    asyncio.run(_test())
