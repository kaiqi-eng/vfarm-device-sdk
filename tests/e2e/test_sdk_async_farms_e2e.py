from __future__ import annotations

import asyncio
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, NotFoundError


def _base_url() -> str:
    return os.environ.get("SDK_E2E_BASE_URL", "http://localhost:8003").rstrip("/")


def _api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required for E2E tests")
    return key


def test_sdk_async_farms_flow() -> None:
    async def _test() -> None:
        suffix = uuid.uuid4().hex[:8]
        farm_id = f"sdk-async-farm-{suffix}"

        async with AsyncVFarmClient(base_url=_base_url(), api_key=_api_key()) as client:
            created = await client.create_farm(
                farm_id=farm_id,
                name="SDK Async Farm",
                description="Created by async farms e2e",
                address="123 Async Way",
            )
            assert created.id == farm_id
            assert created.is_active is True

            fetched = await client.get_farm(farm_id)
            assert fetched.id == farm_id

            updated = await client.update_farm(
                farm_id,
                description="Updated by async farms e2e",
                address="456 Updated Ave",
            )
            assert updated.description == "Updated by async farms e2e"
            assert updated.address == "456 Updated Ave"

            deactivated = await client.deactivate_farm(farm_id)
            assert deactivated.is_active is False
            reactivated = await client.reactivate_farm(farm_id)
            assert reactivated.is_active is True

            ensured = await client.ensure_farm(farm_id=farm_id, name="No Override")
            assert ensured.id == farm_id

            listed = await client.list_farms(limit=10)
            assert listed.total >= len(listed.farms)
            assert listed.total >= 1

            iterated = []
            async for farm in client.iter_farms(page_size=5):
                iterated.append(farm.id)
                if len(iterated) >= 20:
                    break
            assert len(iterated) >= 1

            await client.delete_farm(farm_id)
            try:
                await client.get_farm(farm_id)
                raise AssertionError("Expected NotFoundError after delete_farm")
            except NotFoundError:
                pass

    asyncio.run(_test())
