from __future__ import annotations

from .exceptions import ConflictError
from .models import (
    DeviceThresholdCreate,
    DeviceThresholdListResponse,
    DeviceThresholdResponse,
    DeviceThresholdUpdate,
)


class AsyncDeviceThresholdsApiMixin:
    async def list_device_thresholds(self, device_id: str) -> DeviceThresholdListResponse:
        data = await self._request("GET", f"/api/v1/devices/{device_id}/thresholds")
        return DeviceThresholdListResponse.model_validate(data)

    async def get_device_threshold(self, device_id: str, metric: str) -> DeviceThresholdResponse:
        data = await self._request("GET", f"/api/v1/devices/{device_id}/thresholds/{metric}")
        return DeviceThresholdResponse.model_validate(data)

    async def create_device_threshold(self, device_id: str, payload: DeviceThresholdCreate) -> DeviceThresholdResponse:
        data = await self._request(
            "POST",
            f"/api/v1/devices/{device_id}/thresholds",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceThresholdResponse.model_validate(data)

    async def update_device_threshold(
        self,
        device_id: str,
        metric: str,
        payload: DeviceThresholdUpdate,
    ) -> DeviceThresholdResponse:
        data = await self._request(
            "PATCH",
            f"/api/v1/devices/{device_id}/thresholds/{metric}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceThresholdResponse.model_validate(data)

    async def delete_device_threshold(self, device_id: str, metric: str) -> None:
        await self._request("DELETE", f"/api/v1/devices/{device_id}/thresholds/{metric}")

    async def set_metric_limits(
        self,
        device_id: str,
        *,
        metric: str,
        min_value: float | None = None,
        max_value: float | None = None,
        severity: str = "warning",
        cooldown_minutes: int = 15,
        enabled: bool = True,
    ) -> DeviceThresholdResponse:
        try:
            return await self.create_device_threshold(
                device_id,
                DeviceThresholdCreate(
                    metric=metric,
                    min_value=min_value,
                    max_value=max_value,
                    severity=severity,
                    cooldown_minutes=cooldown_minutes,
                    enabled=enabled,
                ),
            )
        except ConflictError:
            return await self.update_device_threshold(
                device_id,
                metric,
                DeviceThresholdUpdate(
                    min_value=min_value,
                    max_value=max_value,
                    severity=severity,
                    cooldown_minutes=cooldown_minutes,
                    enabled=enabled,
                ),
            )

    async def set_temperature_limits(
        self,
        device_id: str,
        *,
        min_c: float | None = None,
        max_c: float | None = None,
        severity: str = "warning",
        cooldown_minutes: int = 15,
        enabled: bool = True,
    ) -> DeviceThresholdResponse:
        return await self.set_metric_limits(
            device_id,
            metric="temperature",
            min_value=min_c,
            max_value=max_c,
            severity=severity,
            cooldown_minutes=cooldown_minutes,
            enabled=enabled,
        )
