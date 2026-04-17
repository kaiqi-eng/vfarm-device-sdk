from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, DeviceCapabilityCreate, DeviceCapabilityUpdate, DeviceCreate, DeviceLocation


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


async def _sensor_type_for_devices(client: AsyncVFarmClient) -> str:
    preferred = _sensor_type()
    try:
        await client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        return preferred
    except Exception:
        pass

    listing = await client._request("GET", "/api/v1/sensor-types", params={"limit": 200, "offset": 0}, timeout=60.0)
    rows = listing.get("sensor_types", [])
    if not rows:
        raise RuntimeError("No sensor types available for async device registration E2E tests")

    active_row = next((row for row in rows if row.get("is_active") is True), None)
    return (active_row or rows[0])["id"]


async def _sensor_type_for_device_capabilities(client: AsyncVFarmClient) -> str:
    preferred = _sensor_type()
    try:
        sensor_type = await client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        if sensor_type.get("capabilities"):
            return preferred
    except Exception:
        pass

    listing = await client._request("GET", "/api/v1/sensor-types", params={"limit": 200, "offset": 0}, timeout=60.0)
    for row in listing.get("sensor_types", []):
        sensor_type_id = row.get("id")
        if not sensor_type_id:
            continue
        try:
            sensor_type = await client._request("GET", f"/api/v1/sensor-types/{sensor_type_id}", timeout=60.0)
            if sensor_type.get("capabilities"):
                return sensor_type_id
        except Exception:
            continue

    raise RuntimeError("No sensor type with at least one capability was found for async device capability E2E tests")


def test_sdk_async_device_capabilities_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-dc-farm-{suffix}"
        device_id = f"sdk-async-dc-dev-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            sensor_type = await _sensor_type_for_device_capabilities(client)
            await client.ensure_farm(
                farm_id=farm_id,
                name="SDK Async Device Capability Farm",
                description="Async device capabilities tests",
            )
            await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id=sensor_type,
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-cap", node_id="node-cap", position="pc"),
                    firmware_version="1.0.0",
                )
            )

            initial = await client.list_device_capabilities(device_id)
            assert initial.device_id == device_id
            assert initial.total >= 1
            target_capability = initial.capabilities[0].capability_id

            created = await client.create_device_capability_override(
                device_id,
                payload=DeviceCapabilityCreate(
                    capability_id=target_capability,
                    calibration_offset=0.4,
                    calibration_scale=1.01,
                    custom_min=-5.0,
                    custom_max=45.0,
                    enabled=True,
                    notes="capability override async e2e",
                ),
            )
            assert created.capability_id == target_capability
            assert created.source == "device_override"

            updated = await client.update_device_capability_override(
                device_id,
                target_capability,
                DeviceCapabilityUpdate(
                    calibration_offset=0.2,
                    calibration_scale=0.99,
                    notes="updated capability override async",
                ),
            )
            assert updated.calibration_offset == 0.2
            assert updated.calibration_scale == 0.99

            upserted = await client.upsert_device_capability_override(
                device_id,
                capability_id=target_capability,
                calibration_offset=0.1,
                calibration_scale=1.0,
                custom_min=-3.0,
                custom_max=40.0,
                enabled=True,
                notes="upsert override async",
            )
            assert upserted.custom_min == -3.0
            assert upserted.custom_max == 40.0

            calibrated = await client.calibrate_device_capability(
                device_id,
                target_capability,
                offset=0.05,
                scale=1.0,
                notes="calibration helper async",
            )
            assert calibrated.calibration_offset == 0.05

            listed_after = await client.list_device_capabilities(device_id)
            target_rows = [c for c in listed_after.capabilities if c.capability_id == target_capability]
            assert len(target_rows) >= 1
            assert target_rows[0].source in ("device_override", "sensor_type", "legacy")

            await client.delete_device_capability_override(device_id, target_capability)
            listed_final = await client.list_device_capabilities(device_id)
            target_final = [c for c in listed_final.capabilities if c.capability_id == target_capability]
            assert len(target_final) >= 1

    asyncio.run(_test())
