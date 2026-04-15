from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import (
    AsyncVFarmClient,
    AutomationCommandSpec,
    AutomationRuleCreate,
    AutomationRuleUpdate,
    ConditionSimple,
    DeviceCreate,
    DeviceLocation,
    NotFoundError,
)


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def _sensor_type() -> str:
    return os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")


def test_sdk_async_automation_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-auto-farm-{suffix}"
        source_device_id = f"sdk-async-auto-src-{suffix}"
        target_device_id = f"sdk-async-auto-tgt-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            await client.ensure_farm(
                farm_id=farm_id,
                name="SDK Async Automation Farm",
                description="Async automation tests",
            )
            await client.ensure_device(
                DeviceCreate(
                    id=source_device_id,
                    farm_id=farm_id,
                    device_type="sensor",
                    sensor_type_id=_sensor_type(),
                    device_model="DHT22",
                    location=DeviceLocation(rack_id="rack-auto", node_id="node-src", position="p-src"),
                    firmware_version="1.0.0",
                )
            )
            await client.ensure_device(
                DeviceCreate(
                    id=target_device_id,
                    farm_id=farm_id,
                    device_type="actuator",
                    device_model="RelayBoard",
                    location=DeviceLocation(rack_id="rack-auto", node_id="node-tgt", position="p-tgt"),
                    firmware_version="1.0.0",
                )
            )

            created = await client.create_automation_rule(
                AutomationRuleCreate(
                    name=f"SDK Async Automation {suffix}",
                    description="Created by async automation E2E",
                    source_device_ids=[source_device_id],
                    source_farm_ids=[farm_id],
                    trigger_on="reading",
                    conditions=ConditionSimple(metric="temperature", operator=">", value=20.0),
                    target_device_ids=[target_device_id],
                    commands=[AutomationCommandSpec(command_type="restart_service", payload={"reason": "automation-async-e2e"})],
                    cooldown_seconds=30,
                    cooldown_scope="rule",
                    enabled=True,
                    priority=100,
                )
            )
            assert created.id
            rule_id = created.id

            listed = await client.list_automation_rules(limit=200)
            assert any(r.id == rule_id for r in listed.rules)

            fetched = await client.get_automation_rule(rule_id)
            assert fetched.id == rule_id
            assert fetched.trigger_on == "reading"

            disabled = await client.disable_automation_rule(rule_id)
            assert disabled.enabled is False
            enabled = await client.enable_automation_rule(rule_id)
            assert enabled.enabled is True

            updated = await client.update_automation_rule(
                rule_id,
                AutomationRuleUpdate(
                    description="Updated by async automation E2E",
                    priority=90,
                ),
            )
            assert updated.description == "Updated by async automation E2E"
            assert updated.priority == 90

            stats = await client.get_automation_stats()
            assert stats.total_rules >= 1

            history = await client.list_automation_history(rule_id=rule_id, limit=20)
            assert history.total >= 0

            iterated_rules: list[str] = []
            async for row in client.iter_automation_rules(page_size=50):
                iterated_rules.append(row.id)
                if len(iterated_rules) >= 500:
                    break
            assert rule_id in iterated_rules

            iterated_history = []
            async for row in client.iter_automation_history(page_size=50):
                iterated_history.append(row.id)
                if len(iterated_history) >= 500:
                    break
            assert len(iterated_history) >= 0

            await client.delete_automation_rule(rule_id)
            try:
                await client.get_automation_rule(rule_id)
                raise AssertionError("Expected NotFoundError after delete_automation_rule")
            except NotFoundError:
                pass

    asyncio.run(_test())
