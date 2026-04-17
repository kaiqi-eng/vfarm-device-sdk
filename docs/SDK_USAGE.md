# SDK Usage Guide

Comprehensive guide for using `vfarm-device-sdk` to interact with the `vfarm` API.

## Requirements

- Python `3.10+`
- A running `vfarm` API (local Docker or deployed)
- Valid `FARM_API_KEY`

## Installation

Editable install (recommended for development):

```bash
pip install -e .
```

Package install (if published to your package index):

```bash
pip install vfarm-device-sdk
```

## Quick start

```python
from vfarm_device_sdk import DeviceCreate, DeviceLocation, VFarmClient

with VFarmClient(
    base_url="http://localhost:8003",
    api_key="your-farm-api-key",
) as client:
    result = client.ensure_device(
        DeviceCreate(
            id="sensor-001",
            farm_id="farm-alpha",
            device_type="sensor",
            sensor_type_id="dht22",
            device_model="DHT22",
            location=DeviceLocation(rack_id="rack-a", node_id="node-1", position="p1"),
            firmware_version="1.0.0",
        )
    )
    print(result.created, result.device.id)
```

## Async client (alerts + automation + capability groups + capabilities + devices + commands + device capabilities + events + farms + ingestion + readings + sensor types + thresholds)

`AsyncVFarmClient` is now available for alerts, automation, capability groups, capabilities, device, command, device capabilities, events, farms, ingestion, readings, sensor type, and thresholds endpoints with async lifecycle support.

```python
import asyncio
from vfarm_device_sdk import AsyncVFarmClient, DeviceCreate

async def main() -> None:
    async with AsyncVFarmClient(
        base_url="http://localhost:8003",
        api_key="your-farm-api-key",
    ) as client:
        result = await client.ensure_device(
            DeviceCreate(
                id="sensor-async-001",
                farm_id="farm-alpha",
                device_type="sensor",
            )
        )
        print(result.device.id, result.created)

        cmd = await client.enqueue_set_value(
            result.device.id,
            target="fan-speed",
            value=35.0,
            unit="percent",
        )
        print(cmd.id, cmd.command_type)

        health = await client.health()
        print(health["status"])

        latest = await client.get_latest_reading(result.device.id)
        print(latest.id, latest.sensor_id)

        latest_event = await client.get_latest_device_event(result.device.id)
        print(latest_event.event_type if latest_event else "no events")

        farms = await client.list_farms(limit=5)
        print(farms.total)

        threshold = await client.set_temperature_limits(result.device.id, min_c=18.0, max_c=30.0)
        print(threshold.metric, threshold.max_value)

        capabilities = await client.list_device_capabilities(result.device.id)
        print(capabilities.total)

asyncio.run(main())
```

## Client lifecycle

- Use `with VFarmClient(...) as client:` for automatic connection cleanup.
- Or create a client manually and call `client.close()` when finished.

```python
client = VFarmClient(base_url="http://localhost:8003", api_key="...")
try:
    print(client.health())
finally:
    client.close()
```

## ID format rules

Some SDK models enforce different ID patterns. The most common mismatch is using a device-style ID for sensor types.

- `DeviceCreate.id` accepts letters, numbers, underscore, and hyphen (example: `sensor-001`).
- `SensorTypeCreate.id` must be lowercase and underscore-only after the first letter (pattern: `^[a-z][a-z0-9_]*$`; example: `dht22`, `sdk_type_1`).

If a sensor type ID contains a hyphen (for example `st-1`), Pydantic raises a validation error before the API call is made.

## Device APIs

Methods:

- `register_device(payload)`
- `get_device(device_id)`
- `list_devices(farm_id=None, status=None, device_type=None, health_below=None, limit=100, offset=0)`
- `update_device(device_id, payload)`
- `delete_device(device_id)`
- `ensure_device(payload)` (registers, or returns existing on `409`)

Example:

```python
from vfarm_device_sdk import DeviceCreate, DeviceUpdate, DeviceLocation

created = client.register_device(
    DeviceCreate(
        id="sensor-002",
        farm_id="farm-alpha",
        device_type="sensor",
        sensor_type_id="dht22",
        location=DeviceLocation(rack_id="rack-a", node_id="node-2"),
        firmware_version="1.0.0",
    )
)

device = client.get_device("sensor-002")

updated = client.update_device(
    "sensor-002",
    DeviceUpdate(notes="Installed near intake vent")
)

devices = client.list_devices(farm_id="farm-alpha", limit=50)
client.delete_device("sensor-002")
```

## Ingestion APIs

Low-level method:

- `ingest(payload, auto_register=False, idempotency_key=None)`

High-level convenience wrapper:

- `ingest_reading(sensor_id=..., sensor_type=..., farm_id=..., rack_id=..., node_id=..., firmware=..., temperature_value=..., humidity_value=..., ...)`
- `ingest_reading(..., idempotency_key=None)`

Use low-level `ingest` if you already construct `IngestRequest`.
Use `ingest_reading` for simpler call sites.

Example:

```python
ingest_result = client.ingest_reading(
    sensor_id="sensor-001",
    sensor_type="dht22",
    farm_id="farm-alpha",
    rack_id="rack-a",
    node_id="node-1",
    firmware="1.0.0",
    temperature_value=24.6,
    humidity_value=57.3,
    uptime_s=120,
    wifi_rssi=-55,
    auto_register=False,
)
print(ingest_result.id, ingest_result.received_at)
```

## Idempotency keys and safe retries

Use idempotency keys for write operations that might be retried after timeouts/transient failures.

- Header sent by SDK: `Idempotency-Key`
- Helper: `generate_idempotency_key(prefix=None)`
- Behavior: SDK forwards the key; duplicate-prevention safety depends on backend endpoint semantics.

Sync example:

```python
from vfarm_device_sdk import CommandCreate, VFarmClient, generate_idempotency_key

with VFarmClient(base_url="http://localhost:8003", api_key="...") as client:
    key = generate_idempotency_key("command")
    command = client.create_command(
        "sensor-001",
        CommandCreate(command_type="custom", payload={"action": "sync_profile"}),
        idempotency_key=key,
    )
    print(command.id)
```

Async example:

```python
from vfarm_device_sdk import AsyncVFarmClient, generate_idempotency_key

async with AsyncVFarmClient(base_url="http://localhost:8003", api_key="...") as client:
    key = generate_idempotency_key("ingest")
    result = await client.ingest_reading(
        sensor_id="sensor-001",
        sensor_type="dht22",
        farm_id="farm-alpha",
        rack_id="rack-a",
        node_id="node-1",
        firmware="1.0.0",
        temperature_value=24.6,
        humidity_value=57.3,
        idempotency_key=key,
    )
    print(result.id)
```

Safe-to-retry matrix:

| Operation | Default retry safety | With `idempotency_key` | Notes |
| --- | --- | --- | --- |
| `GET/HEAD/OPTIONS/DELETE` | Safe by default | N/A | Idempotent/read-only semantics. |
| `create_command` | Not safe by default | Conditionally safer | Use key for duplicate suppression when endpoint semantics support dedupe. |
| `ingest` / `ingest_reading` | Not safe by default | Conditionally safer | Use key when retrying sensor submissions. |
| `create_automation_rule` | Not safe by default | Conditionally safer | Use key to reduce duplicate rule creation risk. |
| `create_alert_channel` | Not safe by default | Conditionally safer | Use key to reduce duplicate channel creation risk. |
| `create_alert_rule` | Not safe by default | Conditionally safer | Use key to reduce duplicate rule creation risk. |
| Other `POST/PATCH` writes | Not safe by default | Conditionally safer | Safety depends on endpoint dedupe behavior. |

## Farm APIs

Methods:

- `list_farms(is_active=None, limit=100, offset=0)`
- `get_farm(farm_id)`
- `create_farm(farm_id, name, description=None, address=None)`
- `update_farm(farm_id, name=None, description=None, address=None, is_active=None)`
- `delete_farm(farm_id)`
- `reactivate_farm(farm_id)`
- `deactivate_farm(farm_id)`
- `ensure_farm(farm_id=..., name=..., description=None, address=None)`
- `iter_farms(is_active=None, page_size=100)`

Example:

```python
farm = client.ensure_farm(
    farm_id="farm-alpha",
    name="Farm Alpha",
    description="Primary farm",
)

farm = client.update_farm("farm-alpha", address="123 Greenhouse Rd")
print(farm.id, farm.is_active)
```

## Device events APIs

Methods:

- `get_device_events(device_id, event_type=None, severity=None, limit=100, offset=0)`
- `iter_device_events(device_id, event_type=None, severity=None, page_size=100)`
- `get_latest_device_event(device_id, event_type=None, severity=None)`

Example:

```python
events = client.get_device_events("sensor-001", limit=20)
print(events.total)

latest = client.get_latest_device_event("sensor-001")
if latest:
    print(latest.event_type, latest.severity, latest.occurred_at)
```

## Device thresholds APIs

Methods:

- `list_device_thresholds(device_id)`
- `get_device_threshold(device_id, metric)`
- `create_device_threshold(device_id, payload)`
- `update_device_threshold(device_id, metric, payload)`
- `delete_device_threshold(device_id, metric)`
- `set_metric_limits(device_id, metric=..., min_value=None, max_value=None, severity=\"warning\", cooldown_minutes=15, enabled=True)`
- `set_temperature_limits(device_id, min_c=None, max_c=None, severity=\"warning\", cooldown_minutes=15, enabled=True)`

Example:

```python
from vfarm_device_sdk import DeviceThresholdCreate, DeviceThresholdUpdate

created = client.create_device_threshold(
    "sensor-001",
    DeviceThresholdCreate(
        metric="temperature",
        min_value=18.0,
        max_value=30.0,
        severity="warning",
        cooldown_minutes=10,
        enabled=True,
    ),
)

updated = client.update_device_threshold(
    "sensor-001",
    "temperature",
    DeviceThresholdUpdate(max_value=32.0, severity="error"),
)

helper = client.set_temperature_limits("sensor-001", min_c=16.0, max_c=31.0)
print(created.metric, updated.max_value, helper.cooldown_minutes)
```

## Device capabilities APIs

Methods:

- `list_device_capabilities(device_id)`
- `create_device_capability_override(device_id, payload)`
- `update_device_capability_override(device_id, capability_id, payload)`
- `delete_device_capability_override(device_id, capability_id)`
- `upsert_device_capability_override(device_id, capability_id=..., calibration_offset=0.0, calibration_scale=1.0, custom_min=None, custom_max=None, enabled=True, notes=None)`
- `calibrate_device_capability(device_id, capability_id, offset=0.0, scale=1.0, notes=None)`

Example:

```python
from vfarm_device_sdk import DeviceCapabilityCreate, DeviceCapabilityUpdate

caps = client.list_device_capabilities("sensor-001")
target = caps.capabilities[0].capability_id

created = client.create_device_capability_override(
    "sensor-001",
    DeviceCapabilityCreate(
        capability_id=target,
        calibration_offset=0.2,
        calibration_scale=1.01,
        custom_min=-3.0,
        custom_max=40.0,
        enabled=True,
        notes="Install calibration",
    ),
)

updated = client.update_device_capability_override(
    "sensor-001",
    target,
    DeviceCapabilityUpdate(calibration_offset=0.05, calibration_scale=1.0),
)

calibrated = client.calibrate_device_capability("sensor-001", target, offset=0.03, scale=1.0)
print(created.capability_id, updated.calibration_offset, calibrated.source)
```

## Readings and analytics APIs

Methods:

- `get_latest_reading(sensor_id)`
- `list_readings(sensor_id, from_time=None, to_time=None, limit=100, status=None)`
- `get_reading_stats(sensor_id, window="24h")` where window is `1h | 6h | 24h | 7d | 30d`
- `get_readings_analytics(sensor_id, window="24h", recent_limit=100)`

Example:

```python
latest = client.get_latest_reading("sensor-001")
history = client.list_readings("sensor-001", limit=50)
stats = client.get_reading_stats("sensor-001", window="1h")

snapshot = client.get_readings_analytics("sensor-001", window="1h", recent_limit=50)
print(snapshot.sensor_id, snapshot.stats.total_readings)
```

## Command layer APIs

Reader polling and command execution support:

- `fetch_pending_commands(device_id, limit=10)`
- `list_device_commands(device_id, status=None, limit=50, offset=0)`
- `create_command(device_id, payload)`
- `create_command(device_id, payload, idempotency_key=None)`
- `update_command_status(device_id, command_id, payload)`
- `cancel_command(device_id, command_id)`

Convenience command helpers:

- `enqueue_config_update(device_id, changes=..., merge_strategy="patch", priority=100, ttl_minutes=60, notes=None, idempotency_key=None)`
- `enqueue_restart_service(device_id, reason=None, delay_seconds=5, graceful=True, priority=100, ttl_minutes=60, notes=None, idempotency_key=None)`
- `enqueue_set_state(device_id, target=..., state="on"|"off", reason=None, priority=100, ttl_minutes=60, notes=None, payload_extra=None, idempotency_key=None)`
- `enqueue_set_value(device_id, target=..., value=..., unit=None, reason=None, priority=100, ttl_minutes=60, notes=None, payload_extra=None, idempotency_key=None)`
- `enqueue_custom(device_id, action=..., params=None, reason=None, priority=100, ttl_minutes=60, notes=None, payload_extra=None, idempotency_key=None)`

`payload_extra` is merged after typed payload fields and can override keys with the same name.

Example:

```python
from vfarm_device_sdk import CommandAcknowledge

cmd = client.enqueue_config_update(
    "sensor-001",
    changes={"poll_interval_s": 45, "api_timeout_s": 10},
)

pending = client.fetch_pending_commands("sensor-001", limit=5)
target = next(c for c in pending.commands if c.id == cmd.id)

client.update_command_status(
    "sensor-001",
    target.id,
    CommandAcknowledge(status="acknowledged"),
)

client.update_command_status(
    "sensor-001",
    target.id,
    CommandAcknowledge(status="completed", result={"applied": {"poll_interval_s": 45}}),
)

set_state = client.enqueue_set_state(
    "sensor-001",
    target="relay-1",
    state="on",
    payload_extra={"source": "policy-engine"},
)

set_value = client.enqueue_set_value(
    "sensor-001",
    target="fan-speed",
    value=42.0,
    unit="percent",
)

custom = client.enqueue_custom(
    "sensor-001",
    action="sync_profile",
    params={"profile": "eco"},
    payload_extra={"dry_run": True},
)
```

## Error handling

SDK exceptions:

- `AuthenticationError` (`401`)
- `NotFoundError` (`404`)
- `ConflictError` (`409`)
- `ValidationError` (`400`/`422`)
- `VFarmApiError` (other API/network failures)

Pattern:

```python
from vfarm_device_sdk import ConflictError, ValidationError, VFarmApiError

try:
    client.register_device(...)
except ConflictError:
    # Already exists
    ...
except ValidationError as exc:
    print(exc.detail)
except VFarmApiError as exc:
    print(exc.status_code, exc.detail)
```

## Exported models

Commonly used:

- Device models: `DeviceCreate`, `DeviceUpdate`, `DeviceResponse`, `DeviceLocation`
- Device event models: `DeviceEventResponse`, `DeviceEventsListResponse`
- Device threshold models: `DeviceThresholdCreate`, `DeviceThresholdUpdate`, `DeviceThresholdResponse`, `DeviceThresholdListResponse`
- Device capability models: `DeviceCapabilityCreate`, `DeviceCapabilityUpdate`, `DeviceCapabilityResponse`, `DeviceCapabilityListResponse`
- Farm models: `FarmCreate`, `FarmUpdate`, `FarmResponse`, `FarmListResponse`
- Ingestion models: `IngestRequest`, `IngestReading`, `ReadingValue`, `IngestDeviceInfo`
- Readings models: `LatestReadingResponse`, `ReadingsListResponse`, `ReadingStatsResponse`, `ReadingAnalyticsSnapshot`
- Command models: `CommandCreate`, `CommandAcknowledge`, `CommandResponse`, `PendingCommandsResponse`

These are all exported from `vfarm_device_sdk`.

## End-to-end testing

Run all E2E tests:

```bash
FARM_API_KEY=... SDK_E2E_BASE_URL=http://localhost:8003 SDK_E2E_SENSOR_TYPE=dht22 pytest -q tests/e2e
```

Docker-based run (no local Python required):

```bash
docker run --rm --network vfarm_vfarm-network -v "<repo>:/work" -w /work -e FARM_API_KEY=... -e SDK_E2E_BASE_URL=http://api:8000 -e SDK_E2E_SENSOR_TYPE=dht22 python:3.11-slim sh -lc "pip install -e .[dev] && pytest -q tests/e2e"
```

## Project structure

- `python/vfarm_device_sdk/core.py`: shared transport and HTTP error mapping
- `python/vfarm_device_sdk/async_devices.py`: async device API methods
- `python/vfarm_device_sdk/async_commands.py`: async command API methods
- `python/vfarm_device_sdk/async_events.py`: async events API methods
- `python/vfarm_device_sdk/async_farms.py`: async farms API methods
- `python/vfarm_device_sdk/async_ingestion.py`: async ingestion API methods
- `python/vfarm_device_sdk/async_readings.py`: async readings API methods
- `python/vfarm_device_sdk/async_alerts.py`: async alerts API methods
- `python/vfarm_device_sdk/async_automation.py`: async automation API methods
- `python/vfarm_device_sdk/async_capability_groups.py`: async capability groups API methods
- `python/vfarm_device_sdk/async_capabilities.py`: async capabilities API methods
- `python/vfarm_device_sdk/async_sensor_types.py`: async sensor type API methods
- `python/vfarm_device_sdk/async_thresholds.py`: async thresholds API methods
- `python/vfarm_device_sdk/async_device_capabilities.py`: async device capabilities API methods
- `python/vfarm_device_sdk/devices.py`: device API methods
- `python/vfarm_device_sdk/events.py`: device events API methods
- `python/vfarm_device_sdk/thresholds.py`: device thresholds API methods
- `python/vfarm_device_sdk/device_capabilities.py`: device capability override API methods
- `python/vfarm_device_sdk/farms.py`: farm API methods
- `python/vfarm_device_sdk/ingestion.py`: ingestion API methods
- `python/vfarm_device_sdk/readings.py`: readings and analytics API methods
- `python/vfarm_device_sdk/commands.py`: command API methods
- `python/vfarm_device_sdk/client.py`: composed `VFarmClient`
- `python/vfarm_device_sdk/async_client.py`: composed `AsyncVFarmClient` (alerts + automation + capability groups + capabilities + device + command + device capabilities + events + farms + ingestion + readings + sensor type + thresholds APIs)
- `python/vfarm_device_sdk/models.py`: typed request/response models
- `python/vfarm_device_sdk/exceptions.py`: SDK exception classes
