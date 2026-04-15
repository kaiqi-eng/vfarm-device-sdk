from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    CapabilityGroupCreate,
    CapabilityGroupListResponse,
    CapabilityGroupResponse,
    CapabilityGroupUpdate,
)


class AsyncCapabilityGroupsApiMixin:
    async def list_capability_groups(self, *, include_inactive: bool = False) -> CapabilityGroupListResponse:
        data = await self._request("GET", "/api/v1/capability-groups", params={"include_inactive": include_inactive})
        return CapabilityGroupListResponse.model_validate(data)

    async def get_capability_group(self, group_id: str) -> CapabilityGroupResponse:
        data = await self._request("GET", f"/api/v1/capability-groups/{quote(group_id, safe='')}")
        return CapabilityGroupResponse.model_validate(data)

    async def create_capability_group(self, payload: CapabilityGroupCreate) -> CapabilityGroupResponse:
        data = await self._request("POST", "/api/v1/capability-groups", json=payload.model_dump(mode="json", exclude_none=True))
        return CapabilityGroupResponse.model_validate(data)

    async def update_capability_group(self, group_id: str, payload: CapabilityGroupUpdate) -> CapabilityGroupResponse:
        data = await self._request(
            "PATCH",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CapabilityGroupResponse.model_validate(data)

    async def delete_capability_group(self, group_id: str) -> None:
        await self._request("DELETE", f"/api/v1/capability-groups/{quote(group_id, safe='')}")

    async def add_capability_to_group(self, group_id: str, capability_id: str, *, display_order: int = 100) -> None:
        await self._request(
            "POST",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
            params={"display_order": display_order},
        )

    async def remove_capability_from_group(self, group_id: str, capability_id: str) -> None:
        await self._request(
            "DELETE",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    async def ensure_capability_group(self, payload: CapabilityGroupCreate) -> CapabilityGroupResponse:
        try:
            return await self.create_capability_group(payload)
        except ConflictError:
            return await self.get_capability_group(payload.id)

    async def iter_capability_groups(self, *, include_inactive: bool = False) -> AsyncIterator[CapabilityGroupResponse]:
        page = await self.list_capability_groups(include_inactive=include_inactive)
        for group in page.groups:
            yield group
