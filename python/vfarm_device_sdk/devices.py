from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdate,
    EnsureDeviceResult,
)


class DeviceApiMixin:
    def register_device(self, payload: DeviceCreate) -> DeviceCreatedResponse:
        data = self._request("POST", "/api/v1/devices", json=payload.model_dump(mode="json", exclude_none=True))
        return DeviceCreatedResponse.model_validate(data)

    def get_device(self, device_id: str) -> DeviceResponse:
        data = self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}")
        return DeviceResponse.model_validate(data)

    def list_devices(
        self,
        *,
        farm_id: str | None = None,
        status: str | None = None,
        device_type: str | None = None,
        health_below: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DeviceListResponse:
        params = {
            "farm_id": farm_id,
            "status": status,
            "device_type": device_type,
            "health_below": health_below,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/devices", params={k: v for k, v in params.items() if v is not None})
        return DeviceListResponse.model_validate(data)

    def update_device(self, device_id: str, payload: DeviceUpdate) -> DeviceResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/devices/{quote(device_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceResponse.model_validate(data)

    def delete_device(self, device_id: str) -> None:
        self._request("DELETE", f"/api/v1/devices/{quote(device_id, safe='')}")

    def ensure_device(self, payload: DeviceCreate) -> EnsureDeviceResult:
        try:
            created = self.register_device(payload)
            device = self.get_device(payload.id)
            return EnsureDeviceResult(created=True, device=device, created_response=created)
        except ConflictError:
            device = self.get_device(payload.id)
            return EnsureDeviceResult(created=False, device=device)
