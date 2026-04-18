from __future__ import annotations

from pydantic import ValidationError
import pytest

from vfarm_device_sdk.models import (
    AutomationCommandSpec,
    AutomationRuleCreate,
    AutomationRuleUpdate,
    ConditionSimple,
    ConfigUpdatePayload,
    CustomPayload,
    RestartServicePayload,
    SetStatePayload,
    SetValuePayload,
)


@pytest.mark.parametrize(
    ("command_type", "payload", "expected_type"),
    [
        ("config_update", {"changes": {"interval": 30}, "merge_strategy": "patch"}, ConfigUpdatePayload),
        ("restart_service", {"reason": "maintenance", "delay_seconds": 2, "graceful": True}, RestartServicePayload),
        ("set_state", {"target": "relay-1", "state": "on", "reason": "rule"}, SetStatePayload),
        ("set_value", {"target": "fan-speed", "value": 42.5, "unit": "percent"}, SetValuePayload),
        ("custom", {"action": "sync_profile", "params": {"profile": "eco"}}, CustomPayload),
    ],
)
def test_automation_command_spec_coerces_dict_payload(command_type: str, payload: dict, expected_type: type) -> None:
    spec = AutomationCommandSpec(command_type=command_type, payload=payload)
    assert isinstance(spec.payload, expected_type)


def test_automation_command_spec_constructor_style_still_works() -> None:
    spec = AutomationCommandSpec(command_type="restart_service", payload={"reason": "legacy-style"})
    assert isinstance(spec.payload, RestartServicePayload)
    assert spec.payload.reason == "legacy-style"


def test_automation_command_spec_rejects_mismatched_payload_model_instance() -> None:
    with pytest.raises(ValidationError):
        AutomationCommandSpec(
            command_type="set_state",
            payload=RestartServicePayload(reason="wrong"),
        )


def test_automation_rule_create_accepts_mixed_typed_specs() -> None:
    rule = AutomationRuleCreate(
        name="Rule A",
        source_device_ids=["dev-a"],
        source_farm_ids=["farm-a"],
        trigger_on="reading",
        conditions=ConditionSimple(metric="temperature", operator=">", value=20.0),
        target_device_ids=["dev-b"],
        commands=[
            AutomationCommandSpec(command_type="set_state", payload={"target": "relay-1", "state": "on"}),
            AutomationCommandSpec(command_type="set_value", payload={"target": "fan-speed", "value": 40.0}),
            AutomationCommandSpec(command_type="custom", payload={"action": "sync_profile"}),
        ],
    )
    assert isinstance(rule.commands[0].payload, SetStatePayload)
    assert isinstance(rule.commands[1].payload, SetValuePayload)
    assert isinstance(rule.commands[2].payload, CustomPayload)


def test_automation_rule_update_accepts_typed_specs() -> None:
    update = AutomationRuleUpdate(
        commands=[
            AutomationCommandSpec(command_type="config_update", payload={"changes": {"sample": 10}}),
            AutomationCommandSpec(command_type="restart_service", payload={"reason": "reload"}),
        ]
    )
    assert isinstance(update.commands, list)
    assert isinstance(update.commands[0].payload, ConfigUpdatePayload)
    assert isinstance(update.commands[1].payload, RestartServicePayload)
