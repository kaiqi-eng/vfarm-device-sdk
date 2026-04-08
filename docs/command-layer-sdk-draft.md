# Command Layer SDK Draft

This draft maps the `vfarm/docs/COMMAND_LAYER_PLAN.md` API/lifecycle design into SDK features.

## Planned Surface in `VFarmClient`

- `fetch_pending_commands(device_id, limit=10)`
- `list_device_commands(device_id, status=None, limit=50, offset=0)`
- `create_command(device_id, payload)`
- `update_command_status(device_id, command_id, payload)`
- `cancel_command(device_id, command_id)`
- `enqueue_config_update(device_id, changes=..., merge_strategy="patch", ...)`
- `enqueue_restart_service(device_id, reason=None, delay_seconds=5, graceful=True, ...)`

## Mapped Models

- `CommandCreate`
- `CommandAcknowledge`
- `CommandResponse`
- `CommandListResponse`
- `PendingCommandsResponse`
- Payload helpers:
  - `ConfigUpdatePayload`
  - `RestartServicePayload`
  - `SetStatePayload`
  - `SetValuePayload`
  - `CustomPayload`

## Design Notes

- Keep command polling (`fetch_pending_commands`) explicit because it mutates backend state (`pending -> delivered`).
- Preserve lifecycle transitions exactly as backend expects:
  - `delivered -> acknowledged|failed`
  - `acknowledged -> completed|failed`
- Provide both low-level generic methods (`create_command`) and high-level helpers (`enqueue_config_update`, `enqueue_restart_service`).
- Keep command payload fields as JSON-friendly dictionaries so the SDK can evolve with backend command types.
