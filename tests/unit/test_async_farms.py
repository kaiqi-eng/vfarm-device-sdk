from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_farms import AsyncFarmApiMixin
from vfarm_device_sdk.exceptions import ConflictError


def _run(coro):
    return asyncio.run(coro)


class _AsyncFarmHarness(AsyncFarmApiMixin):
    def __init__(self, *, create_conflict: bool = False) -> None:
        self.create_conflict = create_conflict
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()
        if method == "POST" and path == "/api/v1/farms":
            if self.create_conflict:
                raise ConflictError("exists", status_code=409)
            return {
                "id": kwargs["json"]["id"],
                "name": kwargs["json"]["name"],
                "description": kwargs["json"].get("description"),
                "address": kwargs["json"].get("address"),
                "is_active": True,
                "device_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        if method == "GET" and path.startswith("/api/v1/farms/"):
            farm_id = path.rsplit("/", 1)[-1]
            return {
                "id": farm_id,
                "name": "Existing Farm",
                "description": None,
                "address": None,
                "is_active": True,
                "device_count": 2,
                "created_at": now,
                "updated_at": now,
            }
        if method == "GET" and path == "/api/v1/farms":
            offset = int(kwargs["params"]["offset"])
            limit = int(kwargs["params"]["limit"])
            farms = [
                {"id": "farm-1", "name": "Farm 1", "description": None, "address": None, "is_active": True, "device_count": 1, "created_at": now, "updated_at": now},
                {"id": "farm-2", "name": "Farm 2", "description": None, "address": None, "is_active": True, "device_count": 2, "created_at": now, "updated_at": now},
                {"id": "farm-3", "name": "Farm 3", "description": None, "address": None, "is_active": False, "device_count": 0, "created_at": now, "updated_at": now},
            ]
            return {"farms": farms[offset : offset + limit], "total": len(farms)}
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_ensure_farm_created_and_existing() -> None:
    created_h = _AsyncFarmHarness()
    created = _run(created_h.ensure_farm(farm_id="farm-new", name="Farm New"))
    assert created.id == "farm-new"

    existing_h = _AsyncFarmHarness(create_conflict=True)
    existing = _run(existing_h.ensure_farm(farm_id="farm-existing", name="Farm Existing"))
    assert existing.id == "farm-existing"
    assert existing.name == "Existing Farm"


def test_async_iter_farms_paginates() -> None:
    harness = _AsyncFarmHarness()

    async def collect_ids() -> list[str]:
        ids: list[str] = []
        async for farm in harness.iter_farms(page_size=2):
            ids.append(farm.id)
        return ids

    ids = _run(collect_ids())
    assert ids == ["farm-1", "farm-2", "farm-3"]
