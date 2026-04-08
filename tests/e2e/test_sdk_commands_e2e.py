from __future__ import annotations

import os
import uuid

from vfarm_device_sdk import CommandAcknowledge, ConflictError, DeviceCreate, DeviceLocation, VFarmClient


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _ensure_farm(client: VFarmClient, farm_id: str) -> None:
    # Use raw request because farm endpoints are not yet modeled in SDK.
    try:
        client._request(
            "POST",
            "/api/v1/farms",
            json={"id": farm_id, "name": "SDK Command E2E Farm", "description": "Command layer tests"},
        )
    except ConflictError:
        # Ignore duplicates.
        pass


def test_sdk_command_layer_flow() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-cmd-farm-{suffix}"
    device_id = f"sdk-cmd-dev-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
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

        created = client.enqueue_config_update(
            device_id,
            changes={"poll_interval_s": 45, "api_timeout_s": 10},
            notes="sdk command test",
        )
        assert created.device_id == device_id
        assert created.command_type == "config_update"
        assert created.status == "pending"

        pending = client.fetch_pending_commands(device_id, limit=10)
        assert pending.device_id == device_id
        assert any(c.id == created.id for c in pending.commands)
        delivered = next(c for c in pending.commands if c.id == created.id)
        assert delivered.status == "delivered"

        acknowledged = client.update_command_status(
            device_id,
            created.id,
            CommandAcknowledge(status="acknowledged"),
        )
        assert acknowledged.status == "acknowledged"

        completed = client.update_command_status(
            device_id,
            created.id,
            CommandAcknowledge(
                status="completed",
                result={"applied": {"poll_interval_s": 45}, "requires_restart": False},
            ),
        )
        assert completed.status == "completed"
        assert completed.result is not None

        pending_restart = client.enqueue_restart_service(
            device_id,
            reason="post-config validation",
            delay_seconds=2,
            graceful=True,
        )
        assert pending_restart.status == "pending"

        client.cancel_command(device_id, pending_restart.id)
        history = client.list_device_commands(device_id, limit=20)
        by_id = {c.id: c for c in history.commands}
        assert by_id[pending_restart.id].status == "cancelled"
