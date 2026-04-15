from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import (
    AsyncVFarmClient,
    SensorTypeCapabilityCreate,
    SensorTypeCreate,
    SensorTypeUpdate,
)


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


async def _capability_id_for_sensor_type_tests(client: AsyncVFarmClient) -> str:
    preferred = _sensor_type()
    try:
        sensor_type = await client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        capabilities = sensor_type.get("capabilities", [])
        if capabilities:
            preferred_ids = {"temperature", "humidity"}
            for cap in capabilities:
                if cap["capability_id"] in preferred_ids:
                    return cap["capability_id"]
            return capabilities[0]["capability_id"]
    except Exception:
        pass

    listing = await client._request("GET", "/api/v1/capabilities", params={"limit": 200, "offset": 0}, timeout=60.0)
    capability_rows = listing.get("capabilities", [])
    if not capability_rows:
        raise RuntimeError("No capabilities found for async sensor-type E2E tests")
    return capability_rows[0]["id"]


def test_sdk_async_sensor_types_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        sensor_type_id = f"sdk_async_type_{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            capability_id = await _capability_id_for_sensor_type_tests(client)

            created = await client.create_sensor_type(
                SensorTypeCreate(
                    id=sensor_type_id,
                    name="SDK Async Sensor Type",
                    manufacturer="SDK Async Labs",
                    description="Created by async sensor type E2E",
                    communication="digital",
                    power_voltage="3.3V",
                    capabilities=[
                        SensorTypeCapabilityCreate(
                            capability_id=capability_id,
                            is_primary=True,
                            notes="primary capability async",
                        )
                    ],
                )
            )
            assert created.id == sensor_type_id
            assert any(c.capability_id == capability_id for c in created.capabilities)

            listed = await client.list_sensor_types(manufacturer="SDK Async Labs", limit=50)
            assert any(st.id == sensor_type_id for st in listed.sensor_types)

            fetched = await client.get_sensor_type(sensor_type_id)
            assert fetched.id == sensor_type_id
            assert fetched.manufacturer == "SDK Async Labs"

            updated = await client.update_sensor_type(
                sensor_type_id,
                SensorTypeUpdate(
                    name="SDK Async Sensor Type Updated",
                    description="Updated by async sensor type E2E",
                ),
            )
            assert updated.name == "SDK Async Sensor Type Updated"
            assert updated.description == "Updated by async sensor type E2E"

            await client.remove_sensor_type_capability(sensor_type_id, capability_id)
            after_remove = await client.get_sensor_type(sensor_type_id)
            assert all(c.capability_id != capability_id for c in after_remove.capabilities)

            await client.delete_sensor_type(sensor_type_id)
            soft_deleted = await client.get_sensor_type(sensor_type_id)
            assert soft_deleted.is_active is False

    asyncio.run(_test())
