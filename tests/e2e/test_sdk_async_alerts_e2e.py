from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import (
    AlertChannelCreate,
    AlertChannelUpdate,
    AlertRuleCreate,
    AlertRuleUpdate,
    AsyncVFarmClient,
    NotFoundError,
)


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def test_sdk_async_alerts_flow() -> None:
    async def _test() -> None:
        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            channel = await client.create_alert_channel(
                AlertChannelCreate(
                    name=f"SDK Async Alert Channel {uuid.uuid4().hex[:6]}",
                    endpoint_url=f"{_base_url()}/api/v1/devices/batch",
                    http_method="POST",
                    headers={"X-SDK-Test": "alerts-async"},
                    timeout_ms=3000,
                    enabled=True,
                )
            )
            assert channel.id

            listed_channels = await client.list_alert_channels(limit=50)
            assert any(c.id == channel.id for c in listed_channels.channels)

            fetched_channel = await client.get_alert_channel(channel.id)
            assert fetched_channel.id == channel.id

            updated_channel = await client.update_alert_channel(
                channel.id,
                AlertChannelUpdate(
                    name=f"{fetched_channel.name} Updated",
                    enabled=False,
                ),
            )
            assert updated_channel.enabled is False

            reenabled_channel = await client.enable_alert_channel(channel.id)
            assert reenabled_channel.enabled is True

            test_result = await client.test_alert_channel(channel.id)
            assert isinstance(test_result.success, bool)

            rule = await client.create_alert_rule(
                AlertRuleCreate(
                    name=f"SDK Async Alert Rule {uuid.uuid4().hex[:6]}",
                    description="Created by SDK async alerts E2E",
                    event_types=["threshold_exceeded"],
                    severities=["warning", "error"],
                    event_category="threshold",
                    cooldown_minutes=5,
                    cooldown_scope="device_event_type",
                    channel_ids=[channel.id],
                    enabled=True,
                    priority=100,
                )
            )
            assert rule.id

            listed_rules = await client.list_alert_rules(limit=50)
            assert any(r.id == rule.id for r in listed_rules.rules)

            fetched_rule = await client.get_alert_rule(rule.id)
            assert fetched_rule.id == rule.id

            updated_rule = await client.update_alert_rule(
                rule.id,
                AlertRuleUpdate(
                    description="Updated by SDK async alerts E2E",
                    enabled=False,
                ),
            )
            assert updated_rule.enabled is False

            reenabled_rule = await client.enable_alert_rule(rule.id)
            assert reenabled_rule.enabled is True

            history = await client.list_alert_history(limit=20)
            assert history.total >= 0

            iter_channels: list[str] = []
            async for c in client.iter_alert_channels(page_size=25):
                iter_channels.append(c.id)
                if len(iter_channels) >= 500:
                    break
            assert channel.id in iter_channels

            iter_rules: list[str] = []
            async for r in client.iter_alert_rules(page_size=25):
                iter_rules.append(r.id)
                if len(iter_rules) >= 500:
                    break
            assert rule.id in iter_rules

            iter_history: list[int] = []
            async for h in client.iter_alert_history(page_size=25):
                iter_history.append(h.id)
                if len(iter_history) >= 500:
                    break
            assert len(iter_history) >= 0

            await client.delete_alert_rule(rule.id)
            try:
                await client.get_alert_rule(rule.id)
                raise AssertionError("Expected NotFoundError after delete_alert_rule")
            except NotFoundError:
                pass

            await client.delete_alert_channel(channel.id)
            try:
                await client.get_alert_channel(channel.id)
                raise AssertionError("Expected NotFoundError after delete_alert_channel")
            except NotFoundError:
                pass

    asyncio.run(_test())
