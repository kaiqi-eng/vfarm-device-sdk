# Bhavfarm Repository Analysis

## What already exists

- The repository already exposes `POST /api/v1/devices` for explicit registration.
- Registration is protected by the `X-Farm-Key` header.
- The API also supports `GET /api/v1/devices/{device_id}` for verification and reconciliation.
- Sensor ingestion at `POST /api/v1/ingest` can optionally auto-register unknown devices via `?auto_register=true`.

## Registration contract

Source files reviewed:

- `bhavfarm/vfarm/api/app/models.py`
- `bhavfarm/vfarm/api/app/main.py`
- `bhavfarm/vfarm/reader/reader.py`
- `bhavfarm/vfarm/scripts/test_device_ingest_e2e.sh`

Observed device registration payload:

```json
{
  "id": "sensor-001",
  "farm_id": "farm-alpha",
  "device_type": "sensor",
  "device_model": "DHT22",
  "sensor_type_id": "optional",
  "parent_device_id": "optional",
  "location": {
    "rack_id": "rack-a",
    "node_id": "node-1",
    "position": "top-left"
  },
  "capabilities": [],
  "firmware_version": "1.0.0",
  "hardware_revision": "rev-a",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "192.168.1.20",
  "config": {},
  "tags": [],
  "notes": "optional"
}
```

Observed server behavior:

- `409` when the device already exists.
- `400` when `farm_id`, `sensor_type_id`, or `parent_device_id` fails validation.
- `401` when `X-Farm-Key` is missing or invalid.
- `201` with `{ id, created_at }` on success.

## SDK implications

- Client registration should be idempotent at the workflow level, even though the endpoint itself is not idempotent.
- A practical edge-client flow is `register -> get`, with `409 -> get` fallback.
- The SDK should keep transport concerns separate from domain methods because later expansion will likely add ingest, command polling, thresholds, and capability management.
- `farm_id` is mandatory, so bootstrap flows will need farm provisioning ahead of device registration.
