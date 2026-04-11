from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from itertools import islice

import pytest

from vfarm_device_sdk import (
    CapabilityCreate,
    CapabilityGroupCreate,
    CapabilityGroupUpdate,
    CapabilityUpdate,
    CommandAcknowledge,
    CommandCreate,
    DeviceBatchCreateItem,
    DeviceCreate,
    DeviceCapabilityCreate,
    DeviceCapabilityUpdate,
    DeviceLocation,
    DeviceThresholdUpdate,
    DeviceUpdate,
    IngestDeviceInfo,
    IngestLocation,
    IngestReading,
    IngestRequest,
    NotFoundError,
    ReadingValue,
    SensorTypeCapabilityCreate,
    SensorTypeCreate,
    SensorTypeUpdate,
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


def _sensor_type_for_ingest(client: VFarmClient) -> str:
    preferred = _sensor_type()
    try:
        sensor_type = client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        capabilities = {c["capability_id"] for c in sensor_type.get("capabilities", [])}
        if {"temperature", "humidity"}.issubset(capabilities):
            return preferred
    except Exception:
        pass

    listing = client._request("GET", "/api/v1/sensor-types", params={"limit": 200, "offset": 0}, timeout=60.0)
    for sensor_type in listing.get("sensor_types", []):
        capabilities = {c["capability_id"] for c in sensor_type.get("capabilities", [])}
        if {"temperature", "humidity"}.issubset(capabilities):
            return sensor_type["id"]

    raise RuntimeError("No sensor type with both temperature and humidity capabilities was found for E2E tests")


def _capability_id_for_sensor_type_tests(client: VFarmClient) -> str:
    preferred = _sensor_type()
    try:
        sensor_type = client._request("GET", f"/api/v1/sensor-types/{preferred}", timeout=60.0)
        capabilities = sensor_type.get("capabilities", [])
        if capabilities:
            preferred_ids = {"temperature", "humidity"}
            for cap in capabilities:
                if cap["capability_id"] in preferred_ids:
                    return cap["capability_id"]
            return capabilities[0]["capability_id"]
    except Exception:
        pass

    listing = client._request("GET", "/api/v1/capabilities", params={"limit": 200, "offset": 0}, timeout=60.0)
    capability_rows = listing.get("capabilities", [])
    if not capability_rows:
        raise RuntimeError("No capabilities found for sensor-type E2E tests")
    return capability_rows[0]["id"]


def _ensure_farm(client: VFarmClient, farm_id: str) -> None:
    client.ensure_farm(
        farm_id=farm_id,
        name="SDK Full E2E Farm",
        description="Full SDK E2E coverage",
    )


def test_sdk_farm_crud_and_helpers() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-only-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        created = client.create_farm(
            farm_id=farm_id,
            name="SDK Farm CRUD",
            description="Created by farm E2E",
            address="123 SDK Lane",
        )
        assert created.id == farm_id
        assert created.is_active is True

        fetched = client.get_farm(farm_id)
        assert fetched.id == farm_id

        updated = client.update_farm(
            farm_id,
            description="Updated by farm E2E",
            address="456 Updated Ave",
        )
        assert updated.description == "Updated by farm E2E"
        assert updated.address == "456 Updated Ave"

        inactive = client.deactivate_farm(farm_id)
        assert inactive.is_active is False
        active = client.reactivate_farm(farm_id)
        assert active.is_active is True

        listed = client.list_farms(limit=10)
        assert listed.total >= len(listed.farms)

        first_iterated = next(client.iter_farms(page_size=1))
        assert first_iterated.id

        ensured = client.ensure_farm(
            farm_id=farm_id,
            name="Should Not Override",
            description="No-op when already exists",
        )
        assert ensured.id == farm_id

        client.delete_farm(farm_id)
        with pytest.raises(NotFoundError):
            client.get_farm(farm_id)


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

        heartbeat = client.send_device_heartbeat(device_id)
        assert heartbeat.device_id == device_id
        assert heartbeat.status == "online"

        metadata = client.get_device_metadata(device_id)
        assert metadata.device_id == device_id
        updated_metadata = client.update_device_metadata(
            device_id,
            {"sdk_label": "device-crud-e2e", "sample_interval_s": 30},
        )
        assert updated_metadata.device_id == device_id
        assert updated_metadata.config["sdk_label"] == "device-crud-e2e"

        client.delete_device(device_id)
        with pytest.raises(NotFoundError):
            client.get_device(device_id)


def test_sdk_device_batch_registration() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_a = f"sdk-batch-a-{suffix}"
    device_b = f"sdk-batch-b-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)

        result = client.register_devices_batch(
            [
                DeviceBatchCreateItem(id=device_a, farm_id=farm_id, device_type="sensor", tags=["batch", "a"]),
                DeviceBatchCreateItem(id=device_b, farm_id=farm_id, device_type="sensor", tags=["batch", "b"]),
            ]
        )

        assert result.created >= 1
        fetched_a = client.get_device(device_a)
        fetched_b = client.get_device(device_b)
        assert fetched_a.id == device_a
        assert fetched_b.id == device_b


def test_sdk_low_level_ingest_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-ingest-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        sensor_type = _sensor_type_for_ingest(client)
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-y", node_id="node-y", position="py"),
                firmware_version="1.0.0",
            )
        )

        ingest = client.ingest(
            IngestRequest(
                schema_version="1.0.0",
                sensor_id=device_id,
                sensor_type=sensor_type,
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

        latest = client.get_latest_reading(device_id)
        assert latest.sensor_id == device_id


def test_sdk_readings_analytics_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-analytics-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        sensor_type = _sensor_type_for_ingest(client)
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-a", node_id="node-a", position="pa"),
                firmware_version="1.0.0",
            )
        )

        client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type,
            farm_id=farm_id,
            rack_id="rack-a",
            node_id="node-a",
            firmware="1.0.0",
            temperature_value=22.4,
            humidity_value=60.1,
            uptime_s=60,
            wifi_rssi=-42,
            auto_register=False,
        )

        latest = client.get_latest_reading(device_id)
        assert latest.sensor_id == device_id

        readings = client.list_readings(device_id, limit=20)
        assert readings.sensor_id == device_id
        assert readings.count >= 1
        assert any(r.id == latest.id for r in readings.readings)

        stats = client.get_reading_stats(device_id, window="1h")
        assert stats.sensor_id == device_id
        assert stats.window == "1h"
        assert stats.total_readings >= 1

        analytics = client.get_readings_analytics(device_id, window="1h", recent_limit=20)
        assert analytics.sensor_id == device_id
        assert analytics.latest is not None
        assert analytics.recent.count >= 1
        assert analytics.stats.total_readings >= 1


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


def test_sdk_device_events_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-events-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-e", node_id="node-e", position="pe"),
                firmware_version="1.0.0",
            )
        )

        client.create_command(
            device_id,
            CommandCreate(
                command_type="restart_service",
                payload={"reason": "events e2e", "delay_seconds": 1, "graceful": True},
                priority=100,
                ttl_minutes=30,
                notes="events coverage",
            ),
        )

        events = client.get_device_events(device_id, limit=20)
        assert events.device_id == device_id
        assert events.total >= len(events.events)
        assert any(e.event_type == "command_created" for e in events.events)

        latest = client.get_latest_device_event(device_id)
        assert latest is not None
        assert latest.device_id == device_id

        first_events = list(islice(client.iter_device_events(device_id, page_size=5), 5))
        assert len(first_events) >= 1


def test_sdk_device_thresholds_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-thresholds-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
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

        created = client.set_temperature_limits(
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

        listed = client.list_device_thresholds(device_id)
        assert listed.device_id == device_id
        assert any(t.metric == "temperature" for t in listed.thresholds)

        fetched = client.get_device_threshold(device_id, "temperature")
        assert fetched.metric == "temperature"
        assert fetched.max_value == 30.0

        updated = client.update_device_threshold(
            device_id,
            "temperature",
            DeviceThresholdUpdate(max_value=32.0, severity="error"),
        )
        assert updated.max_value == 32.0
        assert updated.severity == "error"

        upserted = client.set_metric_limits(
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

        client.delete_device_threshold(device_id, "temperature")
        listed_after_delete = client.list_device_thresholds(device_id)
        assert all(t.metric != "temperature" for t in listed_after_delete.thresholds)


def test_sdk_device_capabilities_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-full-farm-{suffix}"
    device_id = f"sdk-full-capabilities-{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        _ensure_farm(client, farm_id)
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-cap", node_id="node-cap", position="pc"),
                firmware_version="1.0.0",
            )
        )

        initial = client.list_device_capabilities(device_id)
        assert initial.device_id == device_id
        assert initial.total >= 1
        target_capability = initial.capabilities[0].capability_id

        created = client.create_device_capability_override(
            device_id,
            payload=DeviceCapabilityCreate(
                capability_id=target_capability,
                calibration_offset=0.4,
                calibration_scale=1.01,
                custom_min=-5.0,
                custom_max=45.0,
                enabled=True,
                notes="capability override e2e",
            ),
        )
        assert created.capability_id == target_capability
        assert created.source == "device_override"

        updated = client.update_device_capability_override(
            device_id,
            target_capability,
            DeviceCapabilityUpdate(
                calibration_offset=0.2,
                calibration_scale=0.99,
                notes="updated capability override",
            ),
        )
        assert updated.calibration_offset == 0.2
        assert updated.calibration_scale == 0.99

        upserted = client.upsert_device_capability_override(
            device_id,
            capability_id=target_capability,
            calibration_offset=0.1,
            calibration_scale=1.0,
            custom_min=-3.0,
            custom_max=40.0,
            enabled=True,
            notes="upsert override",
        )
        assert upserted.custom_min == -3.0
        assert upserted.custom_max == 40.0

        calibrated = client.calibrate_device_capability(
            device_id,
            target_capability,
            offset=0.05,
            scale=1.0,
            notes="calibration helper",
        )
        assert calibrated.calibration_offset == 0.05

        listed_after = client.list_device_capabilities(device_id)
        target_rows = [c for c in listed_after.capabilities if c.capability_id == target_capability]
        assert len(target_rows) >= 1
        assert target_rows[0].source in ("device_override", "sensor_type", "legacy")

        client.delete_device_capability_override(device_id, target_capability)
        listed_final = client.list_device_capabilities(device_id)
        target_final = [c for c in listed_final.capabilities if c.capability_id == target_capability]
        assert len(target_final) >= 1


def test_sdk_sensor_types_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    sensor_type_id = f"sdk_type_{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        capability_id = _capability_id_for_sensor_type_tests(client)

        created = client.create_sensor_type(
            SensorTypeCreate(
                id=sensor_type_id,
                name="SDK Sensor Type",
                manufacturer="SDK Labs",
                description="Created by sensor type E2E",
                communication="digital",
                power_voltage="3.3V",
                capabilities=[
                    SensorTypeCapabilityCreate(
                        capability_id=capability_id,
                        is_primary=True,
                        notes="primary capability",
                    )
                ],
            )
        )
        assert created.id == sensor_type_id
        assert any(c.capability_id == capability_id for c in created.capabilities)

        listed = client.list_sensor_types(manufacturer="SDK Labs", limit=50)
        assert any(st.id == sensor_type_id for st in listed.sensor_types)

        fetched = client.get_sensor_type(sensor_type_id)
        assert fetched.id == sensor_type_id
        assert fetched.manufacturer == "SDK Labs"

        updated = client.update_sensor_type(
            sensor_type_id,
            SensorTypeUpdate(
                name="SDK Sensor Type Updated",
                description="Updated by sensor type E2E",
            ),
        )
        assert updated.name == "SDK Sensor Type Updated"
        assert updated.description == "Updated by sensor type E2E"

        client.remove_sensor_type_capability(sensor_type_id, capability_id)
        after_remove = client.get_sensor_type(sensor_type_id)
        assert all(c.capability_id != capability_id for c in after_remove.capabilities)

        client.delete_sensor_type(sensor_type_id)
        soft_deleted = client.get_sensor_type(sensor_type_id)
        assert soft_deleted.is_active is False


def test_sdk_capabilities_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    capability_id = f"sdk_cap_{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        created = client.create_capability(
            CapabilityCreate(
                id=capability_id,
                name="SDK Capability",
                description="Created by capabilities E2E",
                category="environmental",
                data_type="numeric",
                unit="celsius",
                unit_symbol="C",
                min_value=-40,
                max_value=125,
                precision=2,
                icon="thermometer",
            )
        )
        assert created.id == capability_id
        assert created.category == "environmental"

        listed = client.list_capabilities(category="environmental", limit=200)
        assert any(c.id == capability_id for c in listed.capabilities)

        fetched = client.get_capability(capability_id)
        assert fetched.id == capability_id
        assert fetched.name == "SDK Capability"

        updated = client.update_capability(
            capability_id,
            CapabilityUpdate(
                name="SDK Capability Updated",
                description="Updated by capabilities E2E",
                min_value=-20,
                max_value=110,
            ),
        )
        assert updated.name == "SDK Capability Updated"
        assert updated.min_value == -20
        assert updated.max_value == 110

        iterated = list(client.iter_capabilities(category="environmental", page_size=50))
        assert any(c.id == capability_id for c in iterated)

        client.delete_capability(capability_id)
        with pytest.raises(NotFoundError):
            client.get_capability(capability_id)


def test_sdk_capability_groups_api() -> None:
    suffix = uuid.uuid4().hex[:8]
    cap_primary_id = f"sdk_grp_cap_a_{suffix}"
    cap_secondary_id = f"sdk_grp_cap_b_{suffix}"
    group_id = f"sdk_group_{suffix}"

    with VFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
        client.create_capability(
            CapabilityCreate(
                id=cap_primary_id,
                name="SDK Group Cap A",
                description="Primary capability for group E2E",
                category="environmental",
                data_type="numeric",
                unit="celsius",
                unit_symbol="C",
                min_value=-10,
                max_value=80,
                precision=1,
            )
        )
        client.create_capability(
            CapabilityCreate(
                id=cap_secondary_id,
                name="SDK Group Cap B",
                description="Secondary capability for group E2E",
                category="environmental",
                data_type="numeric",
                unit="percent_rh",
                unit_symbol="%",
                min_value=0,
                max_value=100,
                precision=1,
            )
        )

        created = client.create_capability_group(
            CapabilityGroupCreate(
                id=group_id,
                name="SDK Capability Group",
                description="Created by capability group E2E",
                icon="gauge",
                display_order=25,
                capability_ids=[cap_primary_id],
            )
        )
        assert created.id == group_id
        assert any(c.capability_id == cap_primary_id for c in created.capabilities)

        listed = client.list_capability_groups()
        assert any(g.id == group_id for g in listed.groups)

        fetched = client.get_capability_group(group_id)
        assert fetched.id == group_id
        assert fetched.name == "SDK Capability Group"

        updated = client.update_capability_group(
            group_id,
            CapabilityGroupUpdate(
                name="SDK Capability Group Updated",
                description="Updated by capability group E2E",
                display_order=30,
            ),
        )
        assert updated.name == "SDK Capability Group Updated"
        assert updated.display_order == 30

        client.add_capability_to_group(group_id, cap_secondary_id, display_order=2)
        fetched_after_add = client.get_capability_group(group_id)
        assert any(c.capability_id == cap_secondary_id for c in fetched_after_add.capabilities)

        client.remove_capability_from_group(group_id, cap_secondary_id)
        fetched_after_remove = client.get_capability_group(group_id)
        assert all(c.capability_id != cap_secondary_id for c in fetched_after_remove.capabilities)

        iterated = list(client.iter_capability_groups())
        assert any(g.id == group_id for g in iterated)

        client.delete_capability_group(group_id)
        deleted = client.get_capability_group(group_id)
        assert deleted.is_active is False

        client.delete_capability(cap_primary_id)
        client.delete_capability(cap_secondary_id)
