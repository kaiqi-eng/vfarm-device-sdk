from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    SensorTypeCreate,
    SensorTypeListResponse,
    SensorTypeResponse,
    SensorTypeUpdate,
)


class SensorTypeApiMixin:
    def list_sensor_types(
        self,
        *,
        communication: str | None = None,
        manufacturer: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> SensorTypeListResponse:
        params = {
            "communication": communication,
            "manufacturer": manufacturer,
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/sensor-types", params={k: v for k, v in params.items() if v is not None})
        return SensorTypeListResponse.model_validate(data)

    def get_sensor_type(self, sensor_type_id: str) -> SensorTypeResponse:
        data = self._request("GET", f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}")
        return SensorTypeResponse.model_validate(data)

    def create_sensor_type(self, payload: SensorTypeCreate) -> SensorTypeResponse:
        data = self._request("POST", "/api/v1/sensor-types", json=payload.model_dump(mode="json", exclude_none=True))
        return SensorTypeResponse.model_validate(data)

    def update_sensor_type(self, sensor_type_id: str, payload: SensorTypeUpdate) -> SensorTypeResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return SensorTypeResponse.model_validate(data)

    def delete_sensor_type(self, sensor_type_id: str) -> None:
        self._request("DELETE", f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}")

    def remove_sensor_type_capability(self, sensor_type_id: str, capability_id: str) -> None:
        self._request(
            "DELETE",
            f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    def ensure_sensor_type(self, payload: SensorTypeCreate) -> SensorTypeResponse:
        try:
            return self.create_sensor_type(payload)
        except ConflictError:
            return self.get_sensor_type(payload.id)
