from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .exceptions import VFarmApiError
from .idempotency import with_idempotency_header
from .models import (
    IngestDeviceInfo,
    IngestErrorInfo,
    IngestLocation,
    IngestReading,
    IngestRequest,
    IngestResponse,
    ReadingValue,
)


class IngestionApiMixin:
    def ingest(
        self,
        payload: IngestRequest,
        *,
        auto_register: bool = False,
        idempotency_key: str | None = None,
    ) -> IngestResponse:
        path = "/api/v1/ingest"
        params = {"auto_register": "true"} if auto_register else None
        data = self._request(
            "POST",
            path,
            params=params,
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return IngestResponse.model_validate(data)

    def ingest_reading(
        self,
        *,
        sensor_id: str,
        sensor_type: str,
        farm_id: str,
        rack_id: str,
        node_id: str,
        firmware: str,
        temperature_value: float | int | None,
        humidity_value: float | int | None,
        temperature_status: str = "ok",
        humidity_status: str = "ok",
        uptime_s: int | None = None,
        wifi_rssi: int | None = None,
        timestamp: datetime | None = None,
        schema_version: str = "1.0.0",
        error_code: str | None = None,
        error_message: str | None = None,
        auto_register: bool = False,
        idempotency_key: str | None = None,
    ) -> IngestResponse:
        payload = IngestRequest(
            schema_version=schema_version,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            location=IngestLocation(
                farm_id=farm_id,
                rack_id=rack_id,
                node_id=node_id,
            ),
            timestamp=timestamp or datetime.now(timezone.utc),
            readings=IngestReading(
                temperature=ReadingValue(
                    value=temperature_value,
                    unit="celsius",
                    status=temperature_status,
                ),
                humidity=ReadingValue(
                    value=humidity_value,
                    unit="percent_rh",
                    status=humidity_status,
                ),
            ),
            device=IngestDeviceInfo(
                firmware=firmware,
                uptime_s=uptime_s,
                wifi_rssi=wifi_rssi,
            ),
            error=(
                IngestErrorInfo(code=error_code, message=error_message)
                if error_code is not None
                else None
            ),
        )
        return self.ingest(payload, auto_register=auto_register, idempotency_key=idempotency_key)

    def health(self) -> dict[str, Any]:
        data = self._request("GET", "/api/v1/health")
        if not isinstance(data, dict):
            raise VFarmApiError("Unexpected health response", detail=data)
        return data
