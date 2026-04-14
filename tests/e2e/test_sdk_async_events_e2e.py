from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, CommandCreate, ConflictError, DeviceCreate, DeviceLocation


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


async def _ensure_farm(client: AsyncVFarmClient, farm_id: str) -> None:
    try:
        await client._request(
            "POST",
            "/api/v1/farms",
            json={"id": farm_id, "name": "SDK Async Events E2E Farm", "description": "Async events tests"},
        )
    except ConflictError:
        pass


def test_sdk_async_events_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-evt-farm-{suffix}"
        device_id = f"sdk-async-evt-dev-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            await _ensure_farm(client, farm_id)
            await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id="dht22",
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-e", node_id="node-e", position="pe"),
                    firmware_version="1.0.0",
                )
            )

            created = await client.create_command(
                device_id,
                CommandCreate(
                    command_type="restart_service",
                    payload={"reason": "async events e2e", "delay_seconds": 1, "graceful": True},
                    priority=100,
                    ttl_minutes=30,
                    notes="async events coverage",
                ),
            )
            assert created.id

            events = await client.get_device_events(device_id, limit=20)
            assert events.device_id == device_id
            assert events.total >= len(events.events)
            assert any(e.event_type == "command_created" for e in events.events)

            latest = await client.get_latest_device_event(device_id)
            assert latest is not None
            assert latest.device_id == device_id

            iterated: list[str] = []
            async for event in client.iter_device_events(device_id, page_size=5):
                iterated.append(event.event_type)
                if len(iterated) >= 5:
                    break
            assert len(iterated) >= 1

    asyncio.run(_test())
