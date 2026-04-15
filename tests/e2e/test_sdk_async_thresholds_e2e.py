from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, DeviceCreate, DeviceLocation, DeviceThresholdUpdate


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


def test_sdk_async_thresholds_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-thr-farm-{suffix}"
        device_id = f"sdk-async-thr-dev-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            await client.ensure_farm(
                farm_id=farm_id,
                name="SDK Async Threshold Farm",
                description="Async thresholds tests",
            )
            await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id=_sensor_type(),
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-t", node_id="node-t", position="pt"),
                    firmware_version="1.0.0",
                )
            )

            created = await client.set_temperature_limits(
                device_id,
                min_c=18.0,
                max_c=30.0,
                severity="warning",
                cooldown_minutes=10,
                enabled=True,
            )
            assert created.metric == "temperature"
            assert created.min_value == 18.0
            assert created.max_value == 30.0

            listed = await client.list_device_thresholds(device_id)
            assert listed.device_id == device_id
            assert any(t.metric == "temperature" for t in listed.thresholds)

            fetched = await client.get_device_threshold(device_id, "temperature")
            assert fetched.metric == "temperature"

            updated = await client.update_device_threshold(
                device_id,
                "temperature",
                DeviceThresholdUpdate(max_value=32.0, severity="error"),
            )
            assert updated.max_value == 32.0
            assert updated.severity == "error"

            upserted = await client.set_metric_limits(
                device_id,
                metric="temperature",
                min_value=16.0,
                max_value=31.0,
                severity="critical",
                cooldown_minutes=5,
                enabled=True,
            )
            assert upserted.min_value == 16.0
            assert upserted.max_value == 31.0
            assert upserted.severity == "critical"

            await client.delete_device_threshold(device_id, "temperature")
            listed_after_delete = await client.list_device_thresholds(device_id)
            assert all(t.metric != "temperature" for t in listed_after_delete.thresholds)

    asyncio.run(_test())
