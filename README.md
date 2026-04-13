# vfarm Device SDK

Python client SDK scaffold for interacting with the Bhavfarm `vfarm` API from edge devices, scripts, or other client-side applications.

## What it covers

The current package is grounded in the implemented API in the `bhavfarm` repository:

- `POST /api/v1/devices`
- `GET /api/v1/devices/{id}`
- `GET /api/v1/devices`
- `PATCH /api/v1/devices/{id}`
- `DELETE /api/v1/devices/{id}`
- `POST /api/v1/devices/{id}/heartbeat`
- `POST /api/v1/devices/batch`
- `GET /api/v1/devices/{id}/metadata`
- `PATCH /api/v1/devices/{id}/metadata`
- `GET /api/v1/devices/{id}/events`
- `GET /api/v1/devices/{id}/thresholds`
- `GET /api/v1/devices/{id}/thresholds/{metric}`
- `POST /api/v1/devices/{id}/thresholds`
- `PATCH /api/v1/devices/{id}/thresholds/{metric}`
- `DELETE /api/v1/devices/{id}/thresholds/{metric}`
- `GET /api/v1/devices/{id}/capabilities`
- `POST /api/v1/devices/{id}/capabilities`
- `PATCH /api/v1/devices/{id}/capabilities/{capability_id}`
- `DELETE /api/v1/devices/{id}/capabilities/{capability_id}`
- `GET /api/v1/sensor-types`
- `GET /api/v1/sensor-types/{id}`
- `POST /api/v1/sensor-types`
- `PATCH /api/v1/sensor-types/{id}`
- `DELETE /api/v1/sensor-types/{id}`
- `DELETE /api/v1/sensor-types/{id}/capabilities/{capability_id}`
- `GET /api/v1/capabilities`
- `GET /api/v1/capabilities/{id}`
- `POST /api/v1/capabilities`
- `PATCH /api/v1/capabilities/{id}`
- `DELETE /api/v1/capabilities/{id}`
- `GET /api/v1/capability-groups`
- `GET /api/v1/capability-groups/{id}`
- `POST /api/v1/capability-groups`
- `PATCH /api/v1/capability-groups/{id}`
- `DELETE /api/v1/capability-groups/{id}`
- `POST /api/v1/capability-groups/{id}/capabilities/{capability_id}`
- `DELETE /api/v1/capability-groups/{id}/capabilities/{capability_id}`
- `GET /api/v1/automation/rules`
- `GET /api/v1/automation/rules/{id}`
- `POST /api/v1/automation/rules`
- `PATCH /api/v1/automation/rules/{id}`
- `DELETE /api/v1/automation/rules/{id}`
- `GET /api/v1/automation/stats`
- `GET /api/v1/automation/history`
- `GET /api/v1/alerts/channels`
- `GET /api/v1/alerts/channels/{id}`
- `POST /api/v1/alerts/channels`
- `PATCH /api/v1/alerts/channels/{id}`
- `DELETE /api/v1/alerts/channels/{id}`
- `POST /api/v1/alerts/channels/{id}/test`
- `GET /api/v1/alerts/rules`
- `GET /api/v1/alerts/rules/{id}`
- `POST /api/v1/alerts/rules`
- `PATCH /api/v1/alerts/rules/{id}`
- `DELETE /api/v1/alerts/rules/{id}`
- `GET /api/v1/alerts/history`
- `GET /api/v1/farms`
- `GET /api/v1/farms/{id}`
- `POST /api/v1/farms`
- `PATCH /api/v1/farms/{id}`
- `DELETE /api/v1/farms/{id}`
- `POST /api/v1/ingest`
- `GET /api/v1/readings/latest`
- `GET /api/v1/readings`
- `GET /api/v1/readings/stats`
- `GET /api/v1/health`
- `GET /api/v1/devices/{id}/commands/pending`
- `GET /api/v1/devices/{id}/commands`
- `POST /api/v1/devices/{id}/commands`
- `PATCH /api/v1/devices/{id}/commands/{cmd_id}`
- `DELETE /api/v1/devices/{id}/commands/{cmd_id}`

## Package layout

- `python/vfarm_device_sdk/core.py`: shared HTTP transport and error mapping
- `python/vfarm_device_sdk/async_devices.py`: async device registration and device management methods
- `python/vfarm_device_sdk/devices.py`: device registration and device management methods
- `python/vfarm_device_sdk/events.py`: device event history methods and iterator helpers
- `python/vfarm_device_sdk/thresholds.py`: device threshold CRUD and convenience helpers
- `python/vfarm_device_sdk/device_capabilities.py`: per-device capability override and calibration helpers
- `python/vfarm_device_sdk/sensor_types.py`: sensor type CRUD and capability unlink methods
- `python/vfarm_device_sdk/capabilities.py`: capability catalog CRUD and iteration helpers
- `python/vfarm_device_sdk/capability_groups.py`: capability group CRUD and membership helpers
- `python/vfarm_device_sdk/automation.py`: automation rule/history/stats methods
- `python/vfarm_device_sdk/alerts.py`: alert channel/rule/history methods
- `python/vfarm_device_sdk/farms.py`: farm CRUD and helper methods
- `python/vfarm_device_sdk/ingestion.py`: ingestion methods and helper wrapper
- `python/vfarm_device_sdk/readings.py`: readings history, latest, stats, and analytics snapshot helpers
- `python/vfarm_device_sdk/commands.py`: command-layer methods for polling, create/update, and cancel
- `python/vfarm_device_sdk/client.py`: facade `VFarmClient` that composes all API mixins
- `python/vfarm_device_sdk/async_client.py`: facade `AsyncVFarmClient` (currently device + command APIs)
- `python/vfarm_device_sdk/models.py`: typed Pydantic request/response models
- `python/vfarm_device_sdk/exceptions.py`: API-specific exceptions
- `examples/register_device.py`: device registration + ingest + latest reading example
- `examples/farms_example.py`: farm CRUD and iteration example
- `examples/readings_analytics_example.py`: latest/history/stats/analytics snapshot example
- `examples/events_example.py`: device event history and iterator example
- `examples/thresholds_example.py`: threshold CRUD and helper example
- `examples/commands_example.py`: command lifecycle example
- `docs/SDK_USAGE.md`: comprehensive usage documentation
- `docs/bhavfarm-analysis.md`: notes from repo analysis

## Install locally

```bash
pip install -e .
```

## Publishing

Trusted publishing workflows are included for TestPyPI and PyPI. See `docs/PUBLISHING.md` for one-time setup and release steps.

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

## Async usage (devices + commands)

```python
from vfarm_device_sdk import AsyncVFarmClient, DeviceCreate

async with AsyncVFarmClient(base_url="http://localhost:8000", api_key="your-api-key") as client:
    result = await client.ensure_device(
        DeviceCreate(
            id="sensor-async-001",
            farm_id="farm-alpha",
            device_type="sensor",
        )
    )
    print(result.device.id, result.created)

    cmd = await client.enqueue_set_state(
        result.device.id,
        target="relay-1",
        state="on",
        payload_extra={"source": "async-example"},
    )
    print(cmd.id, cmd.command_type)
```

## Current client surface

- `register_device(payload)`
- `get_device(device_id)`
- `list_devices(...)`
- `update_device(device_id, payload)`
- `delete_device(device_id)`
- `list_offline_devices(limit=100)`
- `list_unhealthy_devices(threshold=80, limit=100)`
- `send_device_heartbeat(device_id)`
- `register_devices_batch(devices)`
- `get_device_metadata(device_id)`
- `update_device_metadata(device_id, metadata)`
- `ensure_device(payload)`
- `get_device_events(device_id, event_type=None, severity=None, limit=100, offset=0)`
- `iter_device_events(device_id, event_type=None, severity=None, page_size=100)`
- `get_latest_device_event(device_id, event_type=None, severity=None)`
- `list_device_thresholds(device_id)`
- `get_device_threshold(device_id, metric)`
- `create_device_threshold(device_id, payload)`
- `update_device_threshold(device_id, metric, payload)`
- `delete_device_threshold(device_id, metric)`
- `set_metric_limits(device_id, metric, min_value=None, max_value=None, ...)`
- `set_temperature_limits(device_id, min_c=None, max_c=None, ...)`
- `list_device_capabilities(device_id)`
- `create_device_capability_override(device_id, payload)`
- `update_device_capability_override(device_id, capability_id, payload)`
- `delete_device_capability_override(device_id, capability_id)`
- `upsert_device_capability_override(device_id, capability_id, ...)`
- `calibrate_device_capability(device_id, capability_id, offset=..., scale=...)`
- `list_sensor_types(...)`
- `get_sensor_type(sensor_type_id)`
- `create_sensor_type(payload)`
- `update_sensor_type(sensor_type_id, payload)`
- `delete_sensor_type(sensor_type_id)`
- `remove_sensor_type_capability(sensor_type_id, capability_id)`
- `ensure_sensor_type(payload)`
- `list_capabilities(...)`
- `get_capability(capability_id)`
- `create_capability(payload)`
- `update_capability(capability_id, payload)`
- `delete_capability(capability_id)`
- `ensure_capability(payload)`
- `iter_capabilities(...)`
- `list_capability_groups(include_inactive=False)`
- `get_capability_group(group_id)`
- `create_capability_group(payload)`
- `update_capability_group(group_id, payload)`
- `delete_capability_group(group_id)`
- `add_capability_to_group(group_id, capability_id, display_order=100)`
- `remove_capability_from_group(group_id, capability_id)`
- `ensure_capability_group(payload)`
- `iter_capability_groups(include_inactive=False)`
- `list_automation_rules(...)`
- `get_automation_rule(rule_id)`
- `create_automation_rule(payload)`
- `update_automation_rule(rule_id, payload)`
- `delete_automation_rule(rule_id)`
- `enable_automation_rule(rule_id)`
- `disable_automation_rule(rule_id)`
- `get_automation_stats()`
- `list_automation_history(...)`
- `iter_automation_rules(...)`
- `iter_automation_history(...)`
- `list_alert_channels(...)`
- `get_alert_channel(channel_id)`
- `create_alert_channel(payload)`
- `update_alert_channel(channel_id, payload)`
- `delete_alert_channel(channel_id)`
- `test_alert_channel(channel_id)`
- `enable_alert_channel(channel_id)`
- `disable_alert_channel(channel_id)`
- `list_alert_rules(...)`
- `get_alert_rule(rule_id)`
- `create_alert_rule(payload)`
- `update_alert_rule(rule_id, payload)`
- `delete_alert_rule(rule_id)`
- `enable_alert_rule(rule_id)`
- `disable_alert_rule(rule_id)`
- `list_alert_history(...)`
- `iter_alert_channels(...)`
- `iter_alert_rules(...)`
- `iter_alert_history(...)`
- `list_farms(...)`
- `get_farm(farm_id)`
- `create_farm(farm_id, name, description=None, address=None)`
- `update_farm(farm_id, ...)`
- `delete_farm(farm_id)`
- `reactivate_farm(farm_id)`
- `deactivate_farm(farm_id)`
- `ensure_farm(farm_id, name, ...)`
- `iter_farms(...)`
- `ingest(payload, auto_register=False)`
- `ingest_reading(...)` convenience wrapper for `POST /api/v1/ingest`
- `get_latest_reading(sensor_id)`
- `list_readings(sensor_id, from_time=None, to_time=None, limit=100, status=None)`
- `get_reading_stats(sensor_id, window="24h")`
- `get_readings_analytics(sensor_id, window="24h", recent_limit=100)`
- `fetch_pending_commands(device_id, limit=10)`
- `list_device_commands(device_id, status=None, limit=50, offset=0)`
- `create_command(device_id, payload)`
- `update_command_status(device_id, command_id, payload)`
- `cancel_command(device_id, command_id)`
- `enqueue_config_update(device_id, changes=...)`
- `enqueue_restart_service(device_id, ...)`
- `enqueue_set_state(device_id, target=..., state=..., ..., payload_extra=None)`
- `enqueue_set_value(device_id, target=..., value=..., ..., payload_extra=None)`
- `enqueue_custom(device_id, action=..., params=..., ..., payload_extra=None)`
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
- Device events APIs (`get_device_events`, `iter_device_events`, `get_latest_device_event`)
- Device thresholds APIs (`list_device_thresholds`, `get_device_threshold`, `create/update/delete`, helper upserts)
- Device capabilities APIs (`list_device_capabilities`, override CRUD, calibration/upsert helpers)
- Farm CRUD and helper methods
- Ingestion API wrappers (`ingest`, `ingest_reading`)
- Readings/analytics wrappers (`get_latest_reading`, `list_readings`, `get_reading_stats`, `get_readings_analytics`)
- Command layer APIs (poll, create, update, cancel)
- Docker-backed E2E coverage for current feature set

### Phase 2 (complete)

- Capability catalog + group APIs (`/api/v1/capabilities`, `/api/v1/capability-groups`)

### Phase 3 (automation + operations)

- Automation engine SDK module (rules CRUD, history, enable/disable)
- Alerting and webhook configuration APIs
- Advanced command helpers (typed payload builders for `set_state`, `set_value`, `custom`)
- Async client (`httpx.AsyncClient`) for gateways and high-throughput workloads
  - In progress: `AsyncVFarmClient` currently implements device + command APIs with async transport and lifecycle support

### Phase 4 (developer experience)

- Pagination iterators and filtering helpers
- Retry/backoff policies with jitter and idempotency guidance
- Stronger typed payload objects for command and automation flows
- OpenAPI-driven contract checks in CI
