from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, CapabilityCreate, CapabilityGroupCreate, CapabilityGroupUpdate


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def test_sdk_async_capability_groups_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        cap_primary_id = f"sdk_grp_cap_a_{suffix}"
        cap_secondary_id = f"sdk_grp_cap_b_{suffix}"
        group_id = f"sdk_group_{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            await client.create_capability(
                CapabilityCreate(
                    id=cap_primary_id,
                    name="SDK Async Group Cap A",
                    description="Primary capability for async group E2E",
                    category="environmental",
                    data_type="numeric",
                    unit="celsius",
                    unit_symbol="C",
                    min_value=-10,
                    max_value=80,
                    precision=1,
                )
            )
            await client.create_capability(
                CapabilityCreate(
                    id=cap_secondary_id,
                    name="SDK Async Group Cap B",
                    description="Secondary capability for async group E2E",
                    category="environmental",
                    data_type="numeric",
                    unit="percent_rh",
                    unit_symbol="%",
                    min_value=0,
                    max_value=100,
                    precision=1,
                )
            )

            created = await client.create_capability_group(
                CapabilityGroupCreate(
                    id=group_id,
                    name="SDK Async Capability Group",
                    description="Created by async capability group E2E",
                    icon="gauge",
                    display_order=25,
                    capability_ids=[cap_primary_id],
                )
            )
            assert created.id == group_id
            assert any(c.capability_id == cap_primary_id for c in created.capabilities)

            listed = await client.list_capability_groups()
            assert any(g.id == group_id for g in listed.groups)

            fetched = await client.get_capability_group(group_id)
            assert fetched.id == group_id
            assert fetched.name == "SDK Async Capability Group"

            updated = await client.update_capability_group(
                group_id,
                CapabilityGroupUpdate(
                    name="SDK Async Capability Group Updated",
                    description="Updated by async capability group E2E",
                    display_order=30,
                ),
            )
            assert updated.name == "SDK Async Capability Group Updated"
            assert updated.display_order == 30

            await client.add_capability_to_group(group_id, cap_secondary_id, display_order=2)
            fetched_after_add = await client.get_capability_group(group_id)
            assert any(c.capability_id == cap_secondary_id for c in fetched_after_add.capabilities)

            await client.remove_capability_from_group(group_id, cap_secondary_id)
            fetched_after_remove = await client.get_capability_group(group_id)
            assert all(c.capability_id != cap_secondary_id for c in fetched_after_remove.capabilities)

            iterated: list[str] = []
            async for group in client.iter_capability_groups():
                iterated.append(group.id)
                if len(iterated) >= 500:
                    break
            assert group_id in iterated

            await client.delete_capability_group(group_id)
            deleted = await client.get_capability_group(group_id)
            assert deleted.is_active is False

            await client.delete_capability(cap_primary_id)
            await client.delete_capability(cap_secondary_id)

    asyncio.run(_test())
