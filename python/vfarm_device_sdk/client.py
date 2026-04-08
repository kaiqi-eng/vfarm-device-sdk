from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from .exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    VFarmApiError,
)
from .models import (
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdate,
    EnsureDeviceResult,
    IngestDeviceInfo,
    IngestErrorInfo,
    IngestLocation,
    IngestReading,
    IngestRequest,
    IngestResponse,
    ReadingValue,
)


class VFarmClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout, headers=self._default_headers)
        self._owns_client = client is None

    @property
    def _default_headers(self) -> dict[str, str]:
        return {
            "X-Farm-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "VFarmClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

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

    def ingest(self, payload: IngestRequest, *, auto_register: bool = False) -> IngestResponse:
        path = "/api/v1/ingest"
        params = {"auto_register": "true"} if auto_register else None
        data = self._request(
            "POST",
            path,
            params=params,
            json=payload.model_dump(mode="json", exclude_none=True),
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
    ) -> IngestResponse:
        """
        Convenience wrapper around POST /api/v1/ingest.

        This helper builds a valid IngestRequest from scalar arguments and sends
        it through the same ingest endpoint as `ingest(...)`.
        """
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
        return self.ingest(payload, auto_register=auto_register)

    def health(self) -> dict[str, Any]:
        data = self._request("GET", "/api/v1/health")
        if not isinstance(data, dict):
            raise VFarmApiError("Unexpected health response", detail=data)
        return data

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, f"{self.base_url}{path}", **kwargs)
        except httpx.TimeoutException as exc:
            raise VFarmApiError("Request timed out") from exc
        except httpx.HTTPError as exc:
            raise VFarmApiError("Network request failed") from exc

        if response.status_code == 204:
            return None

        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.is_success:
            return payload

        detail = payload.get("detail") if isinstance(payload, dict) else payload

        if response.status_code == 401:
            raise AuthenticationError("Request was not authorized", status_code=401, detail=detail)
        if response.status_code == 404:
            raise NotFoundError("Resource not found", status_code=404, detail=detail)
        if response.status_code == 409:
            raise ConflictError("Resource already exists", status_code=409, detail=detail)
        if response.status_code in (400, 422):
            raise ValidationError("Request validation failed", status_code=response.status_code, detail=detail)

        raise VFarmApiError("API request failed", status_code=response.status_code, detail=detail)
