from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_automation import AsyncAutomationApiMixin
from vfarm_device_sdk.models import AutomationRuleCreate, AutomationRuleUpdate, ConditionSimple


def _run(coro):
    return asyncio.run(coro)


def _rule_payload(rule_id: str, *, enabled: bool = True, description: str = "rule") -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": rule_id,
        "name": "Automation Rule",
        "description": description,
        "source_device_ids": ["dev_a"],
        "source_device_tags": [],
        "source_farm_ids": ["farm_a"],
        "trigger_on": "reading",
        "conditions": {"op": ">", "metric": "temperature", "value": 20.0},
        "target_device_ids": ["dev_b"],
        "commands": [{"command_type": "restart_service", "payload": {"reason": "unit"}}],
        "cooldown_seconds": 30,
        "cooldown_scope": "rule",
        "enabled": enabled,
        "priority": 100,
        "created_at": now,
        "updated_at": now,
    }


def _history_payload(entry_id: int, rule_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": entry_id,
        "rule_id": rule_id,
        "rule_name": "Automation Rule",
        "source_device_id": "dev_a",
        "reading_values": {"temperature": 24.2},
        "conditions_evaluated": [{"metric": "temperature", "operator": ">", "value": 20.0, "result": True}],
        "conditions_met": True,
        "status": "executed",
        "suppression_reason": None,
        "command_ids": ["cmd_1"],
        "commands_created": 1,
        "triggered_at": now,
    }


class _AsyncAutomationHarness(AsyncAutomationApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/automation/rules":
            return _rule_payload("rule_1")
        if method == "GET" and path.startswith("/api/v1/automation/rules/"):
            rule_id = path.rsplit("/", 1)[-1]
            return _rule_payload(rule_id)
        if method == "GET" and path == "/api/v1/automation/rules":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            rules = [_rule_payload("rule_1"), _rule_payload("rule_2"), _rule_payload("rule_3")]
            rows = rules[offset : offset + limit]
            return {"rules": rows, "total": len(rules), "enabled_count": 3, "disabled_count": 0}
        if method == "PATCH" and path.startswith("/api/v1/automation/rules/"):
            rule_id = path.rsplit("/", 1)[-1]
            payload = _rule_payload(rule_id)
            payload.update(kwargs["json"])
            return payload
        if method == "DELETE" and path.startswith("/api/v1/automation/rules/"):
            return None
        if method == "GET" and path == "/api/v1/automation/stats":
            return {
                "total_rules": 3,
                "enabled_rules": 2,
                "disabled_rules": 1,
                "evaluations_24h": 100,
                "triggers_24h": 50,
                "commands_created_24h": 30,
                "suppressions_24h": 5,
            }
        if method == "GET" and path == "/api/v1/automation/history":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            history = [_history_payload(1, "rule_1"), _history_payload(2, "rule_1"), _history_payload(3, "rule_2")]
            rows = history[offset : offset + limit]
            return {"history": rows, "total": len(history)}
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_automation_crud_stats_history() -> None:
    harness = _AsyncAutomationHarness()
    payload = AutomationRuleCreate(
        name="Rule A",
        source_device_ids=["dev_a"],
        source_farm_ids=["farm_a"],
        trigger_on="reading",
        conditions=ConditionSimple(metric="temperature", operator=">", value=20.0),
        target_device_ids=["dev_b"],
        commands=[{"command_type": "restart_service", "payload": {"reason": "unit"}}],
    )

    created = _run(harness.create_automation_rule(payload))
    assert created.id == "rule_1"

    listed = _run(harness.list_automation_rules(limit=10))
    assert listed.total == 3
    assert listed.rules[0].id == "rule_1"

    fetched = _run(harness.get_automation_rule("rule_1"))
    assert fetched.id == "rule_1"

    updated = _run(harness.update_automation_rule("rule_1", AutomationRuleUpdate(description="updated", priority=90)))
    assert updated.description == "updated"
    assert updated.priority == 90

    disabled = _run(harness.disable_automation_rule("rule_1"))
    assert disabled.enabled is False
    enabled = _run(harness.enable_automation_rule("rule_1"))
    assert enabled.enabled is True

    stats = _run(harness.get_automation_stats())
    assert stats.total_rules == 3

    history = _run(harness.list_automation_history(rule_id="rule_1", limit=10))
    assert history.total == 3
    assert history.history[0].rule_id == "rule_1"

    _run(harness.delete_automation_rule("rule_1"))


def test_async_iter_automation_rules_and_history() -> None:
    harness = _AsyncAutomationHarness()

    async def collect() -> tuple[list[str], list[int]]:
        rule_ids: list[str] = []
        async for rule in harness.iter_automation_rules(page_size=2):
            rule_ids.append(rule.id)

        history_ids: list[int] = []
        async for row in harness.iter_automation_history(page_size=2):
            history_ids.append(row.id)
        return rule_ids, history_ids

    rule_ids, history_ids = _run(collect())
    assert rule_ids == ["rule_1", "rule_2", "rule_3"]
    assert history_ids == [1, 2, 3]
