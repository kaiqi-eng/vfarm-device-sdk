from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest

from vfarm_device_sdk import (
    CommandAcknowledge,
    CommandCreate,
    ConflictError,
    DeviceCreate,
    DeviceLocation,
    DeviceUpdate,
    IngestDeviceInfo,
    IngestLocation,
    IngestReading,
    IngestRequest,
    NotFoundError,
    ReadingValue,
    VFarmClient,
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


def _ensure_farm(client: VFarmClient, farm_id: str) -> None:
    try:
        client._request(
            "POST",
            "/api/v1/farms",
            json={"id": farm_id, "name": "SDK Full E2E Farm", "description": "Full SDK E2E coverage"},
        )
    except ConflictError:
        pass


def test_sdk_health_and_device_crud() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-dev-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        health = client.health()
        assert health["status"] == "ok"

        _ensure_farm(client, farm_id)

        created = client.register_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-x", node_id="node-x", position="px"),
                firmware_version="1.2.0",
                tags=["full-e2e"],
            )
        )
        assert created.id == device_id

        updated = client.update_device(
            device_id,
            DeviceUpdate(
                notes="updated by full e2e test",
                tags=["full-e2e", "updated"],
            ),
        )
        assert updated.id == device_id
        assert updated.notes == "updated by full e2e test"

        listed = client.list_devices(farm_id=farm_id, limit=20)
        assert any(d.id == device_id for d in listed.devices)

        client.delete_device(device_id)
        with pytest.raises(NotFoundError):
            client.get_device(device_id)


def test_sdk_low_level_ingest_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-ingest-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-y", node_id="node-y", position="py"),
                firmware_version="1.0.0",
            )
        )

        ingest = client.ingest(
            IngestRequest(
                schema_version="1.0.0",
                sensor_id=device_id,
                sensor_type=_sensor_type(),
                location=IngestLocation(farm_id=farm_id, rack_id="rack-y", node_id="node-y"),
                readings=IngestReading(
                    temperature=ReadingValue(value=23.9, unit="celsius", status="ok"),
                    humidity=ReadingValue(value=58.8, unit="percent_rh", status="ok"),
                ),
                device=IngestDeviceInfo(firmware="1.0.0", uptime_s=50, wifi_rssi=-47),
                timestamp=datetime.now(timezone.utc),
            ),
            auto_register=False,
        )
        assert ingest.id > 0

        latest = client._request("GET", "/api/v1/readings/latest", params={"sensor_id": device_id})
        assert latest["sensor_id"] == device_id


def test_sdk_generic_command_api_and_status_filters() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-cmd-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-z", node_id="node-z", position="pz"),
                firmware_version="1.0.0",
            )
        )

        created = client.create_command(
            device_id,
            CommandCreate(
                command_type="restart_service",
                payload={"reason": "generic command path", "delay_seconds": 1, "graceful": True},
                priority=100,
                ttl_minutes=30,
                notes="full e2e generic command",
            ),
        )
        assert created.status == "pending"

        pending_list = client.list_device_commands(device_id, status="pending", limit=20)
        assert any(c.id == created.id for c in pending_list.commands)

        pending_fetch = client.fetch_pending_commands(device_id, limit=5)
        delivered = next(c for c in pending_fetch.commands if c.id == created.id)
        assert delivered.status == "delivered"

        acknowledged = client.update_command_status(
            device_id,
            created.id,
            CommandAcknowledge(status="acknowledged"),
        )
        assert acknowledged.status == "acknowledged"

        failed = client.update_command_status(
            device_id,
            created.id,
            CommandAcknowledge(
                status="failed",
                error_code="SIM_FAIL",
                error_message="Simulated failure for E2E",
            ),
        )
        assert failed.status == "failed"

        failed_list = client.list_device_commands(device_id, status="failed", limit=20)
        assert any(c.id == created.id for c in failed_list.commands)
