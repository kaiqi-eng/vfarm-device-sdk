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

- `python/vfarm_device_sdk/client.py`: sync HTTP client
- `python/vfarm_device_sdk/models.py`: typed Pydantic request/response models
- `python/vfarm_device_sdk/exceptions.py`: API-specific exceptions
- `examples/register_device.py`: registration + ingest example
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
- `ensure_device()` includes an ingest-based fallback for environments where `POST /api/v1/devices` is broken by DB/API schema drift

## Next steps

- Add async client support for long-running agents and gateways
- Add device commands, thresholds, capabilities, and events APIs
- Add retries with exponential backoff for unstable edge connectivity
- Add higher-level bootstrap helpers for farm provisioning and device activation
