from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, CommandAcknowledge, ConflictError, DeviceCreate, DeviceLocation


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
            json={"id": farm_id, "name": "SDK Async Command E2E Farm", "description": "Async command tests"},
        )
    except ConflictError:
        pass


def test_sdk_async_command_layer_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-cmd-farm-{suffix}"
        device_id = f"sdk-async-cmd-dev-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            await _ensure_farm(client, farm_id)
            await client.ensure_device(
                DeviceCreate(
                    id=device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id="dht22",
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-d", node_id="node-4", position="p4"),
                    firmware_version="1.0.0",
                )
            )

            created = await client.enqueue_config_update(
                device_id,
                changes={"poll_interval_s": 45, "api_timeout_s": 10},
                notes="sdk async command test",
            )
            assert created.device_id == device_id
            assert created.command_type == "config_update"
            assert created.status == "pending"

            pending = await client.fetch_pending_commands(device_id, limit=10)
            assert pending.device_id == device_id
            assert any(c.id == created.id for c in pending.commands)

            acknowledged = await client.update_command_status(
                device_id,
                created.id,
                CommandAcknowledge(status="acknowledged"),
            )
            assert acknowledged.status == "acknowledged"

            completed = await client.update_command_status(
                device_id,
                created.id,
                CommandAcknowledge(
                    status="completed",
                    result={"applied": {"poll_interval_s": 45}, "requires_restart": False},
                ),
            )
            assert completed.status == "completed"

            pending_set_state = await client.enqueue_set_state(
                device_id,
                target="relay-1",
                state="on",
                reason="sdk async helper test",
                payload_extra={"source": "e2e-async"},
            )
            assert pending_set_state.command_type == "set_state"
            assert pending_set_state.payload.get("source") == "e2e-async"

            pending_set_value = await client.enqueue_set_value(
                device_id,
                target="fan-speed",
                value=42.0,
                unit="percent",
            )
            assert pending_set_value.command_type == "set_value"

            pending_custom = await client.enqueue_custom(
                device_id,
                action="sync_profile",
                params={"profile": "eco"},
                payload_extra={"dry_run": True},
            )
            assert pending_custom.command_type == "custom"

            await client.cancel_command(device_id, pending_custom.id)
            history = await client.list_device_commands(device_id, limit=30)
            by_id = {c.id: c for c in history.commands}
            assert by_id[pending_custom.id].status == "cancelled"
            assert by_id[pending_set_state.id].command_type == "set_state"
            assert by_id[pending_set_value.id].command_type == "set_value"

    asyncio.run(_test())
