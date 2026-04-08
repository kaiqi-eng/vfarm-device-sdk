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

- `ingest(payload, auto_register=False)`

High-level convenience wrapper:

- `ingest_reading(sensor_id=..., sensor_type=..., farm_id=..., rack_id=..., node_id=..., firmware=..., temperature_value=..., humidity_value=..., ...)`

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

## Command layer APIs

Reader polling and command execution support:

- `fetch_pending_commands(device_id, limit=10)`
- `list_device_commands(device_id, status=None, limit=50, offset=0)`
- `create_command(device_id, payload)`
- `update_command_status(device_id, command_id, payload)`
- `cancel_command(device_id, command_id)`

Convenience command helpers:

- `enqueue_config_update(device_id, changes=..., merge_strategy="patch", priority=100, ttl_minutes=60, notes=None)`
- `enqueue_restart_service(device_id, reason=None, delay_seconds=5, graceful=True, priority=100, ttl_minutes=60, notes=None)`

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
- Ingestion models: `IngestRequest`, `IngestReading`, `ReadingValue`, `IngestDeviceInfo`
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
- `python/vfarm_device_sdk/devices.py`: device API methods
- `python/vfarm_device_sdk/ingestion.py`: ingestion API methods
- `python/vfarm_device_sdk/commands.py`: command API methods
- `python/vfarm_device_sdk/client.py`: composed `VFarmClient`
- `python/vfarm_device_sdk/models.py`: typed request/response models
- `python/vfarm_device_sdk/exceptions.py`: SDK exception classes
