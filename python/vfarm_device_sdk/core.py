from __future__ import annotations

from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    VFarmApiError,
)


class VFarmApiClient:
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

    def __enter__(self) -> "VFarmApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

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

        detail = self._extract_error_detail(payload)

        if response.status_code == 401:
            raise AuthenticationError("Request was not authorized", status_code=401, detail=detail)
        if response.status_code == 404:
            raise NotFoundError("Resource not found", status_code=404, detail=detail)
        if response.status_code == 409:
            raise ConflictError("Resource already exists", status_code=409, detail=detail)
        if response.status_code in (400, 422):
            raise ValidationError("Request validation failed", status_code=response.status_code, detail=detail)

        raise VFarmApiError("API request failed", status_code=response.status_code, detail=detail)

    @staticmethod
    def _extract_error_detail(payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        if "detail" in payload and payload["detail"] is not None:
            return payload["detail"]

        # Some vfarm endpoints return structured validation errors without `detail`.
        for key in ("reason", "error", "message", "hint"):
            if key in payload and payload[key]:
                return payload
        return payload


class VFarmAsyncApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout, headers=self._default_headers)
        self._owns_client = client is None

    @property
    def _default_headers(self) -> dict[str, str]:
        return {
            "X-Farm-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "VFarmAsyncApiClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, f"{self.base_url}{path}", **kwargs)
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

        detail = VFarmApiClient._extract_error_detail(payload)

        if response.status_code == 401:
            raise AuthenticationError("Request was not authorized", status_code=401, detail=detail)
        if response.status_code == 404:
            raise NotFoundError("Resource not found", status_code=404, detail=detail)
        if response.status_code == 409:
            raise ConflictError("Resource already exists", status_code=409, detail=detail)
        if response.status_code in (400, 422):
            raise ValidationError("Request validation failed", status_code=response.status_code, detail=detail)

        raise VFarmApiError("API request failed", status_code=response.status_code, detail=detail)
