from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    CapabilityCreate,
    CapabilityListResponse,
    CapabilityResponse,
    CapabilityUpdate,
)


class CapabilitiesApiMixin:
    def list_capabilities(
        self,
        *,
        category: str | None = None,
        data_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CapabilityListResponse:
        params = {
            "category": category,
            "data_type": data_type,
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/capabilities", params={k: v for k, v in params.items() if v is not None})
        return CapabilityListResponse.model_validate(data)

    def get_capability(self, capability_id: str) -> CapabilityResponse:
        data = self._request("GET", f"/api/v1/capabilities/{quote(capability_id, safe='')}")
        return CapabilityResponse.model_validate(data)

    def create_capability(self, payload: CapabilityCreate) -> CapabilityResponse:
        data = self._request("POST", "/api/v1/capabilities", json=payload.model_dump(mode="json", exclude_none=True))
        return CapabilityResponse.model_validate(data)

    def update_capability(self, capability_id: str, payload: CapabilityUpdate) -> CapabilityResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/capabilities/{quote(capability_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CapabilityResponse.model_validate(data)

    def delete_capability(self, capability_id: str) -> None:
        self._request("DELETE", f"/api/v1/capabilities/{quote(capability_id, safe='')}")

    def ensure_capability(self, payload: CapabilityCreate) -> CapabilityResponse:
        try:
            return self.create_capability(payload)
        except ConflictError:
            return self.get_capability(payload.id)

    def iter_capabilities(
        self,
        *,
        category: str | None = None,
        data_type: str | None = None,
        is_active: bool | None = None,
        page_size: int = 100,
    ) -> Iterator[CapabilityResponse]:
        offset = 0
        while True:
            page = self.list_capabilities(
                category=category,
                data_type=data_type,
                is_active=is_active,
                limit=page_size,
                offset=offset,
            )
            for capability in page.capabilities:
                yield capability
            offset += len(page.capabilities)
            if offset >= page.total or not page.capabilities:
                break
