from __future__ import annotations

from datetime import datetime, timezone

from vfarm_device_sdk.commands import CommandApiMixin
from vfarm_device_sdk.models import CommandCreate, CommandResponse


class _CommandHarness(CommandApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, CommandCreate]] = []

    def create_command(self, device_id: str, payload: CommandCreate) -> CommandResponse:  # type: ignore[override]
        self.calls.append((device_id, payload))
        now = datetime.now(timezone.utc)
        return CommandResponse(
            id="cmd-test",
            device_id=device_id,
            command_type=payload.command_type,
            payload=payload.payload,
            priority=payload.priority,
            status="pending",
            created_at=now,
            expires_at=now,
        )


def test_enqueue_set_state_builds_typed_payload_and_merges_extra() -> None:
    sdk = _CommandHarness()
    response = sdk.enqueue_set_state(
        "device-1",
        target="relay-1",
        state="on",
        reason="manual override",
        payload_extra={"reason": "override reason", "mode": "forced"},
    )

    assert response.command_type == "set_state"
    assert len(sdk.calls) == 1
    _, payload = sdk.calls[0]
    assert payload.command_type == "set_state"
    assert payload.payload["target"] == "relay-1"
    assert payload.payload["state"] == "on"
    assert payload.payload["reason"] == "override reason"
    assert payload.payload["mode"] == "forced"


def test_enqueue_set_value_builds_typed_payload_and_merges_extra() -> None:
    sdk = _CommandHarness()
    response = sdk.enqueue_set_value(
        "device-2",
        target="fan-speed",
        value=42.5,
        unit="percent",
        reason="load balancing",
        payload_extra={"value": 55.0, "source": "policy"},
    )

    assert response.command_type == "set_value"
    assert len(sdk.calls) == 1
    _, payload = sdk.calls[0]
    assert payload.command_type == "set_value"
    assert payload.payload["target"] == "fan-speed"
    assert payload.payload["value"] == 55.0
    assert payload.payload["unit"] == "percent"
    assert payload.payload["source"] == "policy"


def test_enqueue_custom_builds_typed_payload_and_merges_extra() -> None:
    sdk = _CommandHarness()
    response = sdk.enqueue_custom(
        "device-3",
        action="reconfigure",
        params={"profile": "eco"},
        reason="night mode",
        payload_extra={"action": "reconfigure_v2", "dry_run": True},
    )

    assert response.command_type == "custom"
    assert len(sdk.calls) == 1
    _, payload = sdk.calls[0]
    assert payload.command_type == "custom"
    assert payload.payload["action"] == "reconfigure_v2"
    assert payload.payload["params"] == {"profile": "eco"}
    assert payload.payload["reason"] == "night mode"
    assert payload.payload["dry_run"] is True
