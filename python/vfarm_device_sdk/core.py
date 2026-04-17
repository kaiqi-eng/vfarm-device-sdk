from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import random
import time
from typing import Any, Literal

import httpx

from .exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
    VFarmApiError,
)


def _default_retryable_status_codes() -> set[int]:
    return {429, *range(500, 600)}


def _default_retryable_methods() -> set[str]:
    return {"GET", "HEAD", "OPTIONS", "DELETE"}


@dataclass(frozen=True)
class RetryPolicy:
    enabled: bool = True
    max_retries: int = 3
    base_delay_s: float = 0.2
    max_delay_s: float = 2.0
    jitter: Literal["full"] = "full"
    retryable_status_codes: set[int] = field(default_factory=_default_retryable_status_codes)
    retryable_methods: set[str] = field(default_factory=_default_retryable_methods)
    allow_unsafe_retries: bool = False
    respect_retry_after: bool = True


class VFarmApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        retry_policy: RetryPolicy | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
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

    def _request(self, method: str, path: str, *, retry: bool | None = None, **kwargs: Any) -> Any:
        normalized_method = method.upper()
        should_retry = self._should_retry_method(normalized_method, retry)
        response: httpx.Response | None = None
        max_attempts = self.retry_policy.max_retries + 1 if should_retry else 1

        for attempt in range(max_attempts):
            try:
                response = self._client.request(normalized_method, f"{self.base_url}{path}", **kwargs)
            except httpx.TimeoutException as exc:
                if should_retry and attempt < max_attempts - 1:
                    self._sleep_before_retry(attempt + 1, None)
                    continue
                raise VFarmApiError("Request timed out") from exc
            except httpx.TransportError as exc:
                if should_retry and attempt < max_attempts - 1:
                    self._sleep_before_retry(attempt + 1, None)
                    continue
                raise VFarmApiError("Network request failed") from exc

            if should_retry and attempt < max_attempts - 1 and self._should_retry_status(response.status_code):
                self._sleep_before_retry(attempt + 1, response)
                continue
            break

        if response is None:
            raise VFarmApiError("Network request failed")

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

    def _should_retry_method(self, method: str, retry_override: bool | None) -> bool:
        if retry_override is not None:
            return retry_override
        if not self.retry_policy.enabled:
            return False
        if method in self.retry_policy.retryable_methods:
            return True
        return self.retry_policy.allow_unsafe_retries

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code in self.retry_policy.retryable_status_codes

    def _compute_backoff_delay(self, retry_attempt: int) -> float:
        delay = min(self.retry_policy.max_delay_s, self.retry_policy.base_delay_s * (2 ** (retry_attempt - 1)))
        if self.retry_policy.jitter == "full":
            return random.uniform(0.0, delay)
        return delay

    def _retry_after_delay(self, response: httpx.Response | None) -> float | None:
        if response is None or response.status_code != 429 or not self.retry_policy.respect_retry_after:
            return None

        header = response.headers.get("Retry-After")
        if not header:
            return None

        try:
            seconds = float(header)
            if seconds < 0:
                return None
            return min(seconds, self.retry_policy.max_delay_s)
        except ValueError:
            pass

        try:
            retry_at = parsedate_to_datetime(header)
        except (TypeError, ValueError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        seconds = (retry_at - now).total_seconds()
        if seconds <= 0:
            return 0.0
        return min(seconds, self.retry_policy.max_delay_s)

    def _sleep_before_retry(self, retry_attempt: int, response: httpx.Response | None) -> None:
        delay = self._retry_after_delay(response)
        if delay is None:
            delay = self._compute_backoff_delay(retry_attempt)
        time.sleep(delay)

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
        retry_policy: RetryPolicy | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
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

    async def _request(self, method: str, path: str, *, retry: bool | None = None, **kwargs: Any) -> Any:
        normalized_method = method.upper()
        should_retry = self._should_retry_method(normalized_method, retry)
        response: httpx.Response | None = None
        max_attempts = self.retry_policy.max_retries + 1 if should_retry else 1

        for attempt in range(max_attempts):
            try:
                response = await self._client.request(normalized_method, f"{self.base_url}{path}", **kwargs)
            except httpx.TimeoutException as exc:
                if should_retry and attempt < max_attempts - 1:
                    await self._sleep_before_retry(attempt + 1, None)
                    continue
                raise VFarmApiError("Request timed out") from exc
            except httpx.TransportError as exc:
                if should_retry and attempt < max_attempts - 1:
                    await self._sleep_before_retry(attempt + 1, None)
                    continue
                raise VFarmApiError("Network request failed") from exc

            if should_retry and attempt < max_attempts - 1 and self._should_retry_status(response.status_code):
                await self._sleep_before_retry(attempt + 1, response)
                continue
            break

        if response is None:
            raise VFarmApiError("Network request failed")

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

    def _should_retry_method(self, method: str, retry_override: bool | None) -> bool:
        if retry_override is not None:
            return retry_override
        if not self.retry_policy.enabled:
            return False
        if method in self.retry_policy.retryable_methods:
            return True
        return self.retry_policy.allow_unsafe_retries

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code in self.retry_policy.retryable_status_codes

    def _compute_backoff_delay(self, retry_attempt: int) -> float:
        delay = min(self.retry_policy.max_delay_s, self.retry_policy.base_delay_s * (2 ** (retry_attempt - 1)))
        if self.retry_policy.jitter == "full":
            return random.uniform(0.0, delay)
        return delay

    def _retry_after_delay(self, response: httpx.Response | None) -> float | None:
        if response is None or response.status_code != 429 or not self.retry_policy.respect_retry_after:
            return None

        header = response.headers.get("Retry-After")
        if not header:
            return None

        try:
            seconds = float(header)
            if seconds < 0:
                return None
            return min(seconds, self.retry_policy.max_delay_s)
        except ValueError:
            pass

        try:
            retry_at = parsedate_to_datetime(header)
        except (TypeError, ValueError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        seconds = (retry_at - now).total_seconds()
        if seconds <= 0:
            return 0.0
        return min(seconds, self.retry_policy.max_delay_s)

    async def _sleep_before_retry(self, retry_attempt: int, response: httpx.Response | None) -> None:
        delay = self._retry_after_delay(response)
        if delay is None:
            delay = self._compute_backoff_delay(retry_attempt)
        await asyncio.sleep(delay)
