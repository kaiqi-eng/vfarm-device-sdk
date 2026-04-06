from __future__ import annotations

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
    IngestRequest,
    IngestResponse,
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
