# vfarm Device SDK

Python client SDK scaffold for interacting with the Bhavfarm `vfarm` API from edge devices, scripts, or other client-side applications.

## What it covers

The current package is grounded in the implemented API in the `bhavfarm` repository:

- `POST /api/v1/devices`
- `GET /api/v1/devices/{id}`
- `GET /api/v1/devices`
- `PATCH /api/v1/devices/{id}`
- `DELETE /api/v1/devices/{id}`
- `POST /api/v1/ingest`
- `GET /api/v1/health`

## Package layout

- `python/vfarm_device_sdk/core.py`: shared HTTP transport and error mapping
- `python/vfarm_device_sdk/devices.py`: device registration and device management methods
- `python/vfarm_device_sdk/ingestion.py`: ingestion methods and helper wrapper
- `python/vfarm_device_sdk/commands.py`: command-layer methods for polling, create/update, and cancel
- `python/vfarm_device_sdk/client.py`: facade `VFarmClient` that composes all API mixins
- `python/vfarm_device_sdk/models.py`: typed Pydantic request/response models
- `python/vfarm_device_sdk/exceptions.py`: API-specific exceptions
- `examples/register_device.py`: registration + ingest example
- `docs/SDK_USAGE.md`: comprehensive usage documentation
- `docs/bhavfarm-analysis.md`: notes from repo analysis

## Install locally

```bash
pip install -e .
```

## Basic usage

```python
from vfarm_device_sdk import DeviceCreate, VFarmClient

with VFarmClient(base_url="http://localhost:8000", api_key="your-api-key") as client:
    result = client.ensure_device(
        DeviceCreate(
            id="sensor-001",
            farm_id="farm-alpha",
            device_type="sensor",
            device_model="DHT22",
            firmware_version="1.0.0",
        )
    )

    print(result.device.id, result.created)
```

## Current client surface

- `register_device(payload)`
- `get_device(device_id)`
- `list_devices(...)`
- `update_device(device_id, payload)`
- `delete_device(device_id)`
- `ensure_device(payload)`
- `ingest(payload, auto_register=False)`
- `ingest_reading(...)` convenience wrapper for `POST /api/v1/ingest`
- `fetch_pending_commands(device_id, limit=10)`
- `list_device_commands(device_id, status=None, limit=50, offset=0)`
- `create_command(device_id, payload)`
- `update_command_status(device_id, command_id, payload)`
- `cancel_command(device_id, command_id)`
- `enqueue_config_update(device_id, changes=...)`
- `enqueue_restart_service(device_id, ...)`
- `health()`

## End-to-end tests

Run against a live vfarm API:

```bash
FARM_API_KEY=... SDK_E2E_BASE_URL=http://localhost:8003 pytest -q tests/e2e/test_sdk_e2e.py
```

Or from Docker (no local Python needed):

```bash
docker run --rm --network vfarm_vfarm-network -v "<repo>:/work" -w /work -e FARM_API_KEY=... -e SDK_E2E_BASE_URL=http://api:8000 -e SDK_E2E_SENSOR_TYPE=dht22 python:3.11-slim sh -lc "pip install -e .[dev] && pytest -q tests/e2e/test_sdk_e2e.py"
```

## Design notes

- Auth is handled with `X-Farm-Key`
- Request/response models mirror the backend contract closely
- `ensure_device()` makes registration workflow-level idempotent by handling `409` and then fetching the device
- `ingest()` uses the same payload shape the repo's reader already sends

## SDK roadmap

### Phase 1 (done)

- Core transport + typed errors
- Device registration and lifecycle methods
- Ingestion API wrappers (`ingest`, `ingest_reading`)
- Command layer APIs (poll, create, update, cancel)
- Docker-backed E2E coverage for current feature set

### Phase 2 (next)

- Device events API (`/api/v1/devices/{id}/events`)
- Threshold management API (`/api/v1/devices/{id}/thresholds`)
- Device capabilities API (`/api/v1/devices/{id}/capabilities`)
- Sensor type and capability catalog APIs (`/api/v1/sensor-types`, `/api/v1/capabilities`, `/api/v1/capability-groups`)
- Farm CRUD API (`/api/v1/farms`)

### Phase 3 (automation + operations)

- Automation engine SDK module (rules CRUD, history, enable/disable)
- Alerting and webhook configuration APIs
- Advanced command helpers (typed payload builders for `set_state`, `set_value`, `custom`)
- Async client (`httpx.AsyncClient`) for gateways and high-throughput workloads

### Phase 4 (developer experience)

- Pagination iterators and filtering helpers
- Retry/backoff policies with jitter and idempotency guidance
- Stronger typed payload objects for command and automation flows
- OpenAPI-driven contract checks in CI
