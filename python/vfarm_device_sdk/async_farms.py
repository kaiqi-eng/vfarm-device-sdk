from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import FarmCreate, FarmListResponse, FarmResponse, FarmUpdate


class AsyncFarmApiMixin:
    async def list_farms(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FarmListResponse:
        params = {
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/farms", params={k: v for k, v in params.items() if v is not None})
        return FarmListResponse.model_validate(data)

    async def get_farm(self, farm_id: str) -> FarmResponse:
        data = await self._request("GET", f"/api/v1/farms/{quote(farm_id, safe='')}")
        return FarmResponse.model_validate(data)

    async def create_farm(
        self,
        *,
        farm_id: str,
        name: str,
        description: str | None = None,
        address: str | None = None,
    ) -> FarmResponse:
        payload = FarmCreate(
            id=farm_id,
            name=name,
            description=description,
            address=address,
        )
        data = await self._request("POST", "/api/v1/farms", json=payload.model_dump(mode="json", exclude_none=True))
        return FarmResponse.model_validate(data)

    async def update_farm(
        self,
        farm_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        address: str | None = None,
        is_active: bool | None = None,
    ) -> FarmResponse:
        payload = FarmUpdate(
            name=name,
            description=description,
            address=address,
            is_active=is_active,
        )
        data = await self._request(
            "PATCH",
            f"/api/v1/farms/{quote(farm_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return FarmResponse.model_validate(data)

    async def delete_farm(self, farm_id: str) -> None:
        await self._request("DELETE", f"/api/v1/farms/{quote(farm_id, safe='')}")

    async def reactivate_farm(self, farm_id: str) -> FarmResponse:
        return await self.update_farm(farm_id, is_active=True)

    async def deactivate_farm(self, farm_id: str) -> FarmResponse:
        return await self.update_farm(farm_id, is_active=False)

    async def ensure_farm(
        self,
        *,
        farm_id: str,
        name: str,
        description: str | None = None,
        address: str | None = None,
    ) -> FarmResponse:
        try:
            return await self.create_farm(farm_id=farm_id, name=name, description=description, address=address)
        except ConflictError:
            return await self.get_farm(farm_id)

    async def iter_farms(
        self,
        *,
        is_active: bool | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[FarmResponse]:
        offset = 0
        while True:
            page = await self.list_farms(is_active=is_active, limit=page_size, offset=offset)
            for farm in page.farms:
                yield farm
            offset += len(page.farms)
            if offset >= page.total or not page.farms:
                break
