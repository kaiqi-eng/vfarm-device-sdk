from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_alerts import AsyncAlertsApiMixin
from vfarm_device_sdk.models import AlertChannelCreate, AlertChannelUpdate, AlertRuleCreate, AlertRuleUpdate


def _run(coro):
    return asyncio.run(coro)


def _channel_payload(channel_id: str, *, enabled: bool = True) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": channel_id,
        "name": "Alert Channel",
        "channel_type": "webhook",
        "endpoint_url": "https://example.com/hook",
        "http_method": "POST",
        "headers": {"X-Test": "1"},
        "timeout_ms": 3000,
        "auth_type": "none",
        "enabled": enabled,
        "last_success_at": None,
        "last_failure_at": None,
        "failure_count": 0,
        "created_at": now,
        "updated_at": now,
    }


def _rule_payload(rule_id: str, channel_id: str, *, enabled: bool = True) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": rule_id,
        "name": "Alert Rule",
        "description": "Rule description",
        "event_types": ["threshold_exceeded"],
        "severities": ["warning", "error"],
        "event_category": "threshold",
        "cooldown_minutes": 5,
        "cooldown_scope": "device_event_type",
        "channel_ids": [channel_id],
        "enabled": enabled,
        "priority": 100,
        "created_at": now,
        "updated_at": now,
    }


def _history_payload(alert_id: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": alert_id,
        "event_id": 1,
        "device_id": "dev-1",
        "event_type": "threshold_exceeded",
        "rule_id": "rule-1",
        "channel_id": "ch-1",
        "status": "sent",
        "suppression_reason": None,
        "response_code": 200,
        "latency_ms": 50,
        "alerted_at": now,
    }


class _AsyncAlertsHarness(AsyncAlertsApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/alerts/channels":
            return _channel_payload("ch_1")
        if method == "GET" and path.startswith("/api/v1/alerts/channels/"):
            channel_id = path.rsplit("/", 1)[-1]
            return _channel_payload(channel_id)
        if method == "GET" and path == "/api/v1/alerts/channels":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            rows = [_channel_payload("ch_1"), _channel_payload("ch_2")]
            return {"channels": rows[offset : offset + limit], "total": len(rows)}
        if method == "PATCH" and path.startswith("/api/v1/alerts/channels/"):
            channel_id = path.rsplit("/", 1)[-1]
            payload = _channel_payload(channel_id)
            payload.update(kwargs["json"])
            return payload
        if method == "DELETE" and path.startswith("/api/v1/alerts/channels/"):
            return None
        if method == "POST" and path.endswith("/test"):
            return {"success": True, "response_code": 200, "latency_ms": 20, "error": None}
        if method == "POST" and path == "/api/v1/alerts/rules":
            return _rule_payload("rule_1", "ch_1")
        if method == "GET" and path.startswith("/api/v1/alerts/rules/"):
            rule_id = path.rsplit("/", 1)[-1]
            return _rule_payload(rule_id, "ch_1")
        if method == "GET" and path == "/api/v1/alerts/rules":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            rows = [_rule_payload("rule_1", "ch_1"), _rule_payload("rule_2", "ch_1")]
            return {"rules": rows[offset : offset + limit], "total": len(rows)}
        if method == "PATCH" and path.startswith("/api/v1/alerts/rules/"):
            rule_id = path.rsplit("/", 1)[-1]
            payload = _rule_payload(rule_id, "ch_1")
            payload.update(kwargs["json"])
            return payload
        if method == "DELETE" and path.startswith("/api/v1/alerts/rules/"):
            return None
        if method == "GET" and path == "/api/v1/alerts/history":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            rows = [_history_payload(1), _history_payload(2), _history_payload(3)]
            return {"alerts": rows[offset : offset + limit], "total": len(rows)}
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_alerts_crud_and_helpers() -> None:
    harness = _AsyncAlertsHarness()

    created_ch = _run(
        harness.create_alert_channel(
            AlertChannelCreate(
                name="Channel A",
                endpoint_url="https://example.com/hook",
                http_method="POST",
                headers={"X-Test": "1"},
                timeout_ms=3000,
                enabled=True,
            )
        )
    )
    assert created_ch.id == "ch_1"

    listed_channels = _run(harness.list_alert_channels(limit=10))
    assert listed_channels.total == 2

    fetched_ch = _run(harness.get_alert_channel("ch_1"))
    assert fetched_ch.id == "ch_1"

    updated_ch = _run(harness.update_alert_channel("ch_1", AlertChannelUpdate(enabled=False)))
    assert updated_ch.enabled is False

    reenabled_ch = _run(harness.enable_alert_channel("ch_1"))
    assert reenabled_ch.enabled is True

    disabled_ch = _run(harness.disable_alert_channel("ch_1"))
    assert disabled_ch.enabled is False

    tested_ch = _run(harness.test_alert_channel("ch_1"))
    assert tested_ch.success is True

    created_rule = _run(
        harness.create_alert_rule(
            AlertRuleCreate(
                name="Rule A",
                event_types=["threshold_exceeded"],
                severities=["warning"],
                channel_ids=["ch_1"],
                enabled=True,
            )
        )
    )
    assert created_rule.id == "rule_1"

    listed_rules = _run(harness.list_alert_rules(limit=10))
    assert listed_rules.total == 2

    fetched_rule = _run(harness.get_alert_rule("rule_1"))
    assert fetched_rule.id == "rule_1"

    updated_rule = _run(harness.update_alert_rule("rule_1", AlertRuleUpdate(enabled=False)))
    assert updated_rule.enabled is False

    reenabled_rule = _run(harness.enable_alert_rule("rule_1"))
    assert reenabled_rule.enabled is True

    disabled_rule = _run(harness.disable_alert_rule("rule_1"))
    assert disabled_rule.enabled is False

    history = _run(harness.list_alert_history(limit=10))
    assert history.total == 3

    _run(harness.delete_alert_rule("rule_1"))
    _run(harness.delete_alert_channel("ch_1"))


def test_async_alert_create_methods_include_idempotency_header() -> None:
    harness = _AsyncAlertsHarness()

    _run(
        harness.create_alert_channel(
            AlertChannelCreate(
                name="Channel A",
                endpoint_url="https://example.com/hook",
                http_method="POST",
                headers={"X-Test": "1"},
                timeout_ms=3000,
                enabled=True,
            ),
            idempotency_key="alert-ch-key",
        )
    )
    _run(
        harness.create_alert_rule(
            AlertRuleCreate(
                name="Rule A",
                event_types=["threshold_exceeded"],
                severities=["warning"],
                channel_ids=["ch_1"],
                enabled=True,
            ),
            idempotency_key="alert-rule-key",
        )
    )

    create_channel_call = next(c for c in harness.calls if c[0] == "POST" and c[1] == "/api/v1/alerts/channels")
    create_rule_call = next(c for c in harness.calls if c[0] == "POST" and c[1] == "/api/v1/alerts/rules")
    assert create_channel_call[2]["headers"]["Idempotency-Key"] == "alert-ch-key"
    assert create_rule_call[2]["headers"]["Idempotency-Key"] == "alert-rule-key"


def test_async_alert_iterators() -> None:
    harness = _AsyncAlertsHarness()

    async def collect() -> tuple[list[str], list[str], list[int]]:
        channel_ids: list[str] = []
        async for channel in harness.iter_alert_channels(page_size=1):
            channel_ids.append(channel.id)

        rule_ids: list[str] = []
        async for rule in harness.iter_alert_rules(page_size=1):
            rule_ids.append(rule.id)

        alert_ids: list[int] = []
        async for alert in harness.iter_alert_history(page_size=2):
            alert_ids.append(alert.id)
        return channel_ids, rule_ids, alert_ids

    channel_ids, rule_ids, alert_ids = _run(collect())
    assert channel_ids == ["ch_1", "ch_2"]
    assert rule_ids == ["rule_1", "rule_2"]
    assert alert_ids == [1, 2, 3]
