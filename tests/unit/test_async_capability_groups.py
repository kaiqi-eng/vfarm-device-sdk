from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_capability_groups import AsyncCapabilityGroupsApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import CapabilityGroupCreate, CapabilityGroupUpdate


def _run(coro):
    return asyncio.run(coro)


def _group_payload(group_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": group_id,
        "name": "Group",
        "description": "Sample capability group",
        "icon": "gauge",
        "display_order": 100,
        "capabilities": [
            {
                "capability_id": "temperature",
                "capability_name": "Temperature",
                "category": "environmental",
                "data_type": "numeric",
                "unit": "celsius",
                "unit_symbol": "C",
                "display_order": 1,
            }
        ],
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


class _AsyncCapabilityGroupsHarness(AsyncCapabilityGroupsApiMixin):
    def __init__(self, *, create_conflict: bool = False) -> None:
        self.create_conflict = create_conflict
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/capability-groups":
            if self.create_conflict:
                raise ConflictError("exists", status_code=409)
            return _group_payload(kwargs["json"]["id"])
        if method == "GET" and path.startswith("/api/v1/capability-groups/"):
            group_id = path.rsplit("/", 1)[-1]
            return _group_payload(group_id)
        if method == "GET" and path == "/api/v1/capability-groups":
            return {"groups": [_group_payload("group_one"), _group_payload("group_two")], "total": 2}
        if method == "PATCH" and path.startswith("/api/v1/capability-groups/"):
            group_id = path.rsplit("/", 1)[-1]
            payload = _group_payload(group_id)
            payload.update(kwargs["json"])
            return payload
        if method == "POST" and "/capabilities/" in path:
            return None
        if method == "DELETE" and path.startswith("/api/v1/capability-groups/"):
            return None
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_capability_groups_crud_membership_and_ensure() -> None:
    harness = _AsyncCapabilityGroupsHarness()
    payload = CapabilityGroupCreate(
        id="sdk_group",
        name="SDK Group",
        description="Created by unit test",
        icon="gauge",
        display_order=25,
        capability_ids=["temperature"],
    )

    created = _run(harness.create_capability_group(payload))
    assert created.id == "sdk_group"

    listed = _run(harness.list_capability_groups())
    assert listed.total == 2
    assert listed.groups[0].id == "group_one"

    fetched = _run(harness.get_capability_group("sdk_group"))
    assert fetched.id == "sdk_group"

    updated = _run(
        harness.update_capability_group(
            "sdk_group",
            CapabilityGroupUpdate(name="SDK Group Updated", display_order=30),
        )
    )
    assert updated.name == "SDK Group Updated"
    assert updated.display_order == 30

    _run(harness.add_capability_to_group("sdk_group", "humidity", display_order=2))
    _run(harness.remove_capability_from_group("sdk_group", "humidity"))
    _run(harness.delete_capability_group("sdk_group"))

    ensured_created = _run(harness.ensure_capability_group(payload))
    assert ensured_created.id == "sdk_group"

    conflict_harness = _AsyncCapabilityGroupsHarness(create_conflict=True)
    ensured_existing = _run(conflict_harness.ensure_capability_group(payload))
    assert ensured_existing.id == "sdk_group"


def test_async_iter_capability_groups() -> None:
    harness = _AsyncCapabilityGroupsHarness()

    async def collect_ids() -> list[str]:
        ids: list[str] = []
        async for group in harness.iter_capability_groups():
            ids.append(group.id)
        return ids

    ids = _run(collect_ids())
    assert ids == ["group_one", "group_two"]
