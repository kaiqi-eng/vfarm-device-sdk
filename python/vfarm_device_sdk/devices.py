from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    DeviceBatchCreateItem,
    DeviceBatchRegisterResponse,
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceHeartbeatResponse,
    DeviceListResponse,
    DeviceMetadataResponse,
    DeviceMetadataUpdateResponse,
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

    def list_offline_devices(self, *, limit: int = 100) -> DeviceListResponse:
        data = self._request("GET", "/api/v1/devices/offline", params={"limit": limit})
        return DeviceListResponse.model_validate(data)

    def list_unhealthy_devices(self, *, threshold: int = 80, limit: int = 100) -> DeviceListResponse:
        data = self._request("GET", "/api/v1/devices/unhealthy", params={"threshold": threshold, "limit": limit})
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

    def send_device_heartbeat(self, device_id: str) -> DeviceHeartbeatResponse:
        data = self._request("POST", f"/api/v1/devices/{quote(device_id, safe='')}/heartbeat")
        return DeviceHeartbeatResponse.model_validate(data)

    def register_devices_batch(self, devices: list[DeviceBatchCreateItem]) -> DeviceBatchRegisterResponse:
        payload = {"devices": [d.model_dump(mode="json", exclude_none=True) for d in devices]}
        data = self._request("POST", "/api/v1/devices/batch", json=payload)
        return DeviceBatchRegisterResponse.model_validate(data)

    def get_device_metadata(self, device_id: str) -> DeviceMetadataResponse:
        data = self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}/metadata")
        return DeviceMetadataResponse.model_validate(data)

    def update_device_metadata(self, device_id: str, metadata: dict[str, object]) -> DeviceMetadataUpdateResponse:
        data = self._request("PATCH", f"/api/v1/devices/{quote(device_id, safe='')}/metadata", json=metadata)
        return DeviceMetadataUpdateResponse.model_validate(data)

    def ensure_device(self, payload: DeviceCreate) -> EnsureDeviceResult:
        try:
            created = self.register_device(payload)
            device = self.get_device(payload.id)
            return EnsureDeviceResult(created=True, device=device, created_response=created)
        except ConflictError:
            device = self.get_device(payload.id)
            return EnsureDeviceResult(created=False, device=device)
