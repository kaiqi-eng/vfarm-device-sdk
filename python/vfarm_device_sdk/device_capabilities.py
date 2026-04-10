from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    DeviceCapabilityCreate,
    DeviceCapabilityListResponse,
    DeviceCapabilityResponse,
    DeviceCapabilityUpdate,
)


class DeviceCapabilitiesApiMixin:
    def list_device_capabilities(self, device_id: str) -> DeviceCapabilityListResponse:
        data = self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}/capabilities")
        return DeviceCapabilityListResponse.model_validate(data)

    def create_device_capability_override(
        self,
        device_id: str,
        payload: DeviceCapabilityCreate,
    ) -> DeviceCapabilityResponse:
        data = self._request(
            "POST",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceCapabilityResponse.model_validate(data)

    def update_device_capability_override(
        self,
        device_id: str,
        capability_id: str,
        payload: DeviceCapabilityUpdate,
    ) -> DeviceCapabilityResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceCapabilityResponse.model_validate(data)

    def delete_device_capability_override(self, device_id: str, capability_id: str) -> None:
        self._request(
            "DELETE",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    def upsert_device_capability_override(
        self,
        device_id: str,
        *,
        capability_id: str,
        calibration_offset: float = 0.0,
        calibration_scale: float = 1.0,
        custom_min: float | None = None,
        custom_max: float | None = None,
        enabled: bool = True,
        notes: str | None = None,
    ) -> DeviceCapabilityResponse:
        create_payload = DeviceCapabilityCreate(
            capability_id=capability_id,
            calibration_offset=calibration_offset,
            calibration_scale=calibration_scale,
            custom_min=custom_min,
            custom_max=custom_max,
            enabled=enabled,
            notes=notes,
        )
        try:
            return self.create_device_capability_override(device_id, create_payload)
        except ConflictError:
            return self.update_device_capability_override(
                device_id,
                capability_id,
                DeviceCapabilityUpdate(
                    calibration_offset=calibration_offset,
                    calibration_scale=calibration_scale,
                    custom_min=custom_min,
                    custom_max=custom_max,
                    enabled=enabled,
                    notes=notes,
                ),
            )

    def calibrate_device_capability(
        self,
        device_id: str,
        capability_id: str,
        *,
        offset: float = 0.0,
        scale: float = 1.0,
        notes: str | None = None,
    ) -> DeviceCapabilityResponse:
        return self.upsert_device_capability_override(
            device_id,
            capability_id=capability_id,
            calibration_offset=offset,
            calibration_scale=scale,
            notes=notes,
        )
