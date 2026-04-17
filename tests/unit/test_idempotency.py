from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.alerts import AlertsApiMixin
from vfarm_device_sdk.async_commands import AsyncCommandApiMixin
from vfarm_device_sdk.automation import AutomationApiMixin
from vfarm_device_sdk.commands import CommandApiMixin
from vfarm_device_sdk.idempotency import generate_idempotency_key
from vfarm_device_sdk.ingestion import IngestionApiMixin
from vfarm_device_sdk.models import (
    AlertChannelCreate,
    AlertRuleCreate,
    AutomationRuleCreate,
    CommandCreate,
    ConditionSimple,
    IngestRequest,
)


class _CommandHarness(CommandApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": "cmd-1",
            "device_id": "dev-1",
            "command_type": "custom",
            "payload": {},
            "priority": 100,
            "status": "pending",
            "created_at": now,
            "expires_at": now,
        }


class _IngestionHarness(IngestionApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        return {"id": 123, "received_at": datetime.now(timezone.utc).isoformat(), "processing_ms": 11}


class _AlertsHarness(AlertsApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()
        if path == "/api/v1/alerts/channels":
            return {
                "id": "ch-1",
                "name": "Channel A",
                "channel_type": "webhook",
                "endpoint_url": "https://example.com/hook",
                "http_method": "POST",
                "headers": {},
                "timeout_ms": 3000,
                "auth_type": "none",
                "enabled": True,
                "last_success_at": None,
                "last_failure_at": None,
                "failure_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        if path == "/api/v1/alerts/rules":
            return {
                "id": "rule-1",
                "name": "Rule A",
                "description": None,
                "event_types": ["threshold_exceeded"],
                "severities": ["warning"],
                "event_category": None,
                "cooldown_minutes": 5,
                "cooldown_scope": "device_event_type",
                "channel_ids": ["ch-1"],
                "enabled": True,
                "priority": 100,
                "created_at": now,
                "updated_at": now,
            }
        raise AssertionError(f"Unhandled call {method} {path}")


class _AutomationHarness(AutomationApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": "auto-1",
            "name": "Rule A",
            "description": None,
            "source_device_ids": ["dev-1"],
            "source_device_tags": [],
            "source_farm_ids": ["farm-1"],
            "trigger_on": "reading",
            "conditions": {"op": ">", "metric": "temperature", "value": 20.0},
            "target_device_ids": ["dev-2"],
            "commands": [{"command_type": "restart_service", "payload": {"reason": "unit"}}],
            "cooldown_seconds": 30,
            "cooldown_scope": "rule",
            "enabled": True,
            "priority": 100,
            "created_at": now,
            "updated_at": now,
        }


class _AsyncCommandHarness(AsyncCommandApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": "cmd-1",
            "device_id": "dev-1",
            "command_type": "custom",
            "payload": {},
            "priority": 100,
            "status": "pending",
            "created_at": now,
            "expires_at": now,
        }


def test_generate_idempotency_key_without_prefix() -> None:
    from vfarm_device_sdk import generate_idempotency_key as exported

    key = exported()
    assert len(key) == 32
    assert key.isalnum()


def test_generate_idempotency_key_with_normalized_prefix() -> None:
    key = generate_idempotency_key(" Sensor Retry ")
    assert key.startswith("sensor-retry-")
    assert len(key.split("-")[-1]) == 32


def test_generate_idempotency_key_is_unique() -> None:
    key_a = generate_idempotency_key("cmd")
    key_b = generate_idempotency_key("cmd")
    assert key_a != key_b


def test_sync_create_command_sets_idempotency_header_when_provided() -> None:
    harness = _CommandHarness()
    harness.create_command(
        "dev-1",
        CommandCreate(command_type="custom", payload={"action": "noop"}),
        idempotency_key="cmd-key-1",
    )
    _, _, kwargs = harness.calls[0]
    assert kwargs["headers"]["Idempotency-Key"] == "cmd-key-1"


def test_sync_create_command_omits_idempotency_header_when_missing() -> None:
    harness = _CommandHarness()
    harness.create_command("dev-1", CommandCreate(command_type="custom", payload={"action": "noop"}))
    _, _, kwargs = harness.calls[0]
    assert kwargs["headers"] is None


def test_sync_ingest_sets_idempotency_header_when_provided() -> None:
    harness = _IngestionHarness()
    payload = IngestRequest.model_validate(
        {
            "schema_version": "1.0.0",
            "sensor_id": "dev-1",
            "sensor_type": "dht22",
            "location": {"farm_id": "farm-a", "rack_id": "rack-1", "node_id": "node-1"},
            "readings": {
                "temperature": {"value": 24.1, "unit": "celsius", "status": "ok"},
                "humidity": {"value": 59.2, "unit": "percent_rh", "status": "ok"},
            },
            "device": {"firmware": "1.0.0"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    harness.ingest(payload, idempotency_key="ingest-key-1")
    _, _, kwargs = harness.calls[0]
    assert kwargs["headers"]["Idempotency-Key"] == "ingest-key-1"


def test_sync_alert_create_methods_set_idempotency_header() -> None:
    harness = _AlertsHarness()
    harness.create_alert_channel(
        AlertChannelCreate(
            name="Channel A",
            endpoint_url="https://example.com/hook",
            http_method="POST",
            headers={"X-Test": "1"},
            timeout_ms=3000,
            enabled=True,
        ),
        idempotency_key="alert-channel-key",
    )
    harness.create_alert_rule(
        AlertRuleCreate(
            name="Rule A",
            event_types=["threshold_exceeded"],
            severities=["warning"],
            channel_ids=["ch-1"],
            enabled=True,
        ),
        idempotency_key="alert-rule-key",
    )

    assert harness.calls[0][2]["headers"]["Idempotency-Key"] == "alert-channel-key"
    assert harness.calls[1][2]["headers"]["Idempotency-Key"] == "alert-rule-key"


def test_sync_create_automation_rule_sets_idempotency_header() -> None:
    harness = _AutomationHarness()
    harness.create_automation_rule(
        AutomationRuleCreate(
            name="Rule A",
            source_device_ids=["dev-1"],
            source_farm_ids=["farm-1"],
            trigger_on="reading",
            conditions=ConditionSimple(metric="temperature", operator=">", value=20.0),
            target_device_ids=["dev-2"],
            commands=[{"command_type": "restart_service", "payload": {"reason": "unit"}}],
        ),
        idempotency_key="automation-key-1",
    )
    _, _, kwargs = harness.calls[0]
    assert kwargs["headers"]["Idempotency-Key"] == "automation-key-1"


def test_async_create_command_sets_and_omits_idempotency_header() -> None:
    harness = _AsyncCommandHarness()
    payload = CommandCreate(command_type="custom", payload={"action": "noop"})
    asyncio.run(harness.create_command("dev-1", payload, idempotency_key="async-cmd-key"))
    asyncio.run(harness.create_command("dev-1", payload))

    assert harness.calls[0][2]["headers"]["Idempotency-Key"] == "async-cmd-key"
    assert harness.calls[1][2]["headers"] is None
