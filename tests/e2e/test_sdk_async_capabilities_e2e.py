from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, CapabilityCreate, CapabilityUpdate, NotFoundError


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def test_sdk_async_capabilities_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        capability_id = f"sdk_cap_{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            created = await client.create_capability(
                CapabilityCreate(
                    id=capability_id,
                    name="SDK Async Capability",
                    description="Created by async capabilities E2E",
                    category="environmental",
                    data_type="numeric",
                    unit="celsius",
                    unit_symbol="C",
                    min_value=-40,
                    max_value=125,
                    precision=2,
                    icon="thermometer",
                )
            )
            assert created.id == capability_id
            assert created.category == "environmental"

            listed = await client.list_capabilities(category="environmental", limit=200)
            assert any(c.id == capability_id for c in listed.capabilities)

            fetched = await client.get_capability(capability_id)
            assert fetched.id == capability_id
            assert fetched.name == "SDK Async Capability"

            updated = await client.update_capability(
                capability_id,
                CapabilityUpdate(
                    name="SDK Async Capability Updated",
                    description="Updated by async capabilities E2E",
                    min_value=-20,
                    max_value=110,
                ),
            )
            assert updated.name == "SDK Async Capability Updated"
            assert updated.min_value == -20
            assert updated.max_value == 110

            iterated: list[str] = []
            async for capability in client.iter_capabilities(category="environmental", page_size=50):
                iterated.append(capability.id)
                if len(iterated) >= 500:
                    break
            assert capability_id in iterated

            await client.delete_capability(capability_id)
            try:
                await client.get_capability(capability_id)
                raise AssertionError("Expected NotFoundError after delete_capability")
            except NotFoundError:
                pass

    asyncio.run(_test())
