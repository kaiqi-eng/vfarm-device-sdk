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
    """
    Return default HTTP status codes considered retryable.

    Parameters
    ----------
    None
        This function takes no parameters.

    Returns
    -------
    set[int]
        Retryable status code set.

    Examples
    --------
    .. code-block:: python

       codes = _default_retryable_status_codes()
       print(429 in codes)

    Common Errors
    -------------
    - ``N/A`` -> ``None``: Pure helper; does not raise SDK HTTP exceptions.
    """
    return {429, *range(500, 600)}


def _default_retryable_methods() -> set[str]:
    """
    Return default HTTP methods eligible for retries.

    Parameters
    ----------
    None
        This function takes no parameters.

    Returns
    -------
    set[str]
        Retryable method set.

    Examples
    --------
    .. code-block:: python

       methods = _default_retryable_methods()
       print("GET" in methods)

    Common Errors
    -------------
    - ``N/A`` -> ``None``: Pure helper; does not raise SDK HTTP exceptions.
    """
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
        """
        Initialize the synchronous API transport client.

        Parameters
        ----------
        base_url:
            API base URL.
        api_key:
            Farm API key sent as ``X-Farm-Key``.
        timeout:
            Request timeout seconds.
        retry_policy:
            Optional retry policy override.
        client:
            Optional external ``httpx.Client`` instance.

        Returns
        -------
        None
            Configures instance state.

        Examples
        --------
        .. code-block:: python

           client = VFarmApiClient(base_url="http://localhost:8003", api_key="...")

        Common Errors
        -------------
        - ``N/A`` -> ``VFarmApiError``: Network/API exceptions occur later during requests, not initialization.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
        self._client = client or httpx.Client(timeout=timeout, headers=self._default_headers)
        self._owns_client = client is None

    @property
    def _default_headers(self) -> dict[str, str]:
        """
        Build default request headers for API calls.

        Parameters
        ----------
        None
            This property takes no parameters.

        Returns
        -------
        dict[str, str]
            Default HTTP headers.

        Examples
        --------
        .. code-block:: python

           headers = client._default_headers
           print(headers["X-Farm-Key"])

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Property access does not perform I/O.
        """
        return {
            "X-Farm-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def close(self) -> None:
        """
        Close the underlying sync HTTP client when owned by this instance.

        Parameters
        ----------
        None
            This method takes no parameters.

        Returns
        -------
        None
            Closes client resources.

        Examples
        --------
        .. code-block:: python

           client.close()

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "VFarmApiClient":
        """
        Enter context manager for sync client usage.

        Parameters
        ----------
        None
            This method takes no parameters.

        Returns
        -------
        VFarmApiClient
            Current client instance.

        Examples
        --------
        .. code-block:: python

           with VFarmApiClient(base_url="http://localhost:8003", api_key="...") as client:
               print(client.base_url)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Exit context manager and close owned HTTP resources.

        Parameters
        ----------
        exc_type:
            Exception type if raised inside context.
        exc:
            Exception instance if raised inside context.
        tb:
            Traceback object if raised inside context.

        Returns
        -------
        None
            Ensures resource cleanup.

        Examples
        --------
        .. code-block:: python

           with VFarmApiClient(base_url="http://localhost:8003", api_key="..."):
               pass

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        self.close()

    def _request(self, method: str, path: str, *, retry: bool | None = None, **kwargs: Any) -> Any:
        """
        Execute a sync HTTP request with retry and SDK error translation.

        Parameters
        ----------
        method:
            HTTP method.
        path:
            API path relative to ``base_url``.
        retry:
            Optional per-call retry override.
        **kwargs:
            Extra ``httpx`` request keyword arguments.

        Returns
        -------
        Any
            Parsed JSON payload, text payload, or ``None`` for ``204`` responses.

        Examples
        --------
        .. code-block:: python

           payload = client._request("GET", "/api/v1/health")
           print(payload)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Request validation failed.
        - ``401`` -> ``AuthenticationError``: Invalid credentials.
        - ``404`` -> ``NotFoundError``: Resource not found.
        - ``409`` -> ``ConflictError``: Resource conflict.
        - ``429/5xx`` -> ``VFarmApiError``: Retries exhausted or non-mapped failures.
        """
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
        """
        Decide if retries are enabled for an HTTP method.

        Parameters
        ----------
        method:
            HTTP method.
        retry_override:
            Per-call retry override.

        Returns
        -------
        bool
            ``True`` when retries should run.

        Examples
        --------
        .. code-block:: python

           should = client._should_retry_method("GET", None)
           print(should)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        if retry_override is not None:
            return retry_override
        if not self.retry_policy.enabled:
            return False
        if method in self.retry_policy.retryable_methods:
            return True
        return self.retry_policy.allow_unsafe_retries

    def _should_retry_status(self, status_code: int) -> bool:
        """
        Decide if a response status code is retryable.

        Parameters
        ----------
        status_code:
            HTTP response status code.

        Returns
        -------
        bool
            ``True`` when code is configured as retryable.

        Examples
        --------
        .. code-block:: python

           print(client._should_retry_status(503))

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        return status_code in self.retry_policy.retryable_status_codes

    def _compute_backoff_delay(self, retry_attempt: int) -> float:
        """
        Compute exponential backoff delay (with optional jitter).

        Parameters
        ----------
        retry_attempt:
            One-based retry attempt number.

        Returns
        -------
        float
            Delay in seconds.

        Examples
        --------
        .. code-block:: python

           delay = client._compute_backoff_delay(2)
           print(delay)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        delay = min(self.retry_policy.max_delay_s, self.retry_policy.base_delay_s * (2 ** (retry_attempt - 1)))
        if self.retry_policy.jitter == "full":
            return random.uniform(0.0, delay)
        return delay

    def _retry_after_delay(self, response: httpx.Response | None) -> float | None:
        """
        Parse and clamp ``Retry-After`` delay when available.

        Parameters
        ----------
        response:
            HTTP response potentially containing ``Retry-After``.

        Returns
        -------
        float | None
            Delay seconds if usable, otherwise ``None``.

        Examples
        --------
        .. code-block:: python

           delay = client._retry_after_delay(response)
           print(delay)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Parsing failures are handled internally.
        """
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
        """
        Sleep for computed retry delay before another attempt.

        Parameters
        ----------
        retry_attempt:
            One-based retry attempt number.
        response:
            Last response used for ``Retry-After`` parsing.

        Returns
        -------
        None
            Pauses execution for retry backoff.

        Examples
        --------
        .. code-block:: python

           client._sleep_before_retry(1, None)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Delay computation handles missing headers safely.
        """
        delay = self._retry_after_delay(response)
        if delay is None:
            delay = self._compute_backoff_delay(retry_attempt)
        time.sleep(delay)

    @staticmethod
    def _extract_error_detail(payload: Any) -> Any:
        """
        Normalize backend error payloads into a consistent detail object.

        Parameters
        ----------
        payload:
            Parsed response payload.

        Returns
        -------
        Any
            Extracted detail value.

        Examples
        --------
        .. code-block:: python

           detail = VFarmApiClient._extract_error_detail({"detail": "Invalid"})
           print(detail)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure data-normalization helper.
        """
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
        """
        Initialize the asynchronous API transport client.

        Parameters
        ----------
        base_url:
            API base URL.
        api_key:
            Farm API key sent as ``X-Farm-Key``.
        timeout:
            Request timeout seconds.
        retry_policy:
            Optional retry policy override.
        client:
            Optional external ``httpx.AsyncClient`` instance.

        Returns
        -------
        None
            Configures instance state.

        Examples
        --------
        .. code-block:: python

           client = VFarmAsyncApiClient(base_url="http://localhost:8003", api_key="...")

        Common Errors
        -------------
        - ``N/A`` -> ``VFarmApiError``: Network/API exceptions occur later during requests.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
        self._client = client or httpx.AsyncClient(timeout=timeout, headers=self._default_headers)
        self._owns_client = client is None

    @property
    def _default_headers(self) -> dict[str, str]:
        """
        Build default request headers for async API calls.

        Parameters
        ----------
        None
            This property takes no parameters.

        Returns
        -------
        dict[str, str]
            Default HTTP headers.

        Examples
        --------
        .. code-block:: python

           headers = client._default_headers
           print(headers["Content-Type"])

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Property access does not perform I/O.
        """
        return {
            "X-Farm-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def aclose(self) -> None:
        """
        Close the underlying async HTTP client when owned by this instance.

        Parameters
        ----------
        None
            This method takes no parameters.

        Returns
        -------
        None
            Closes client resources.

        Examples
        --------
        .. code-block:: python

           await client.aclose()

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "VFarmAsyncApiClient":
        """
        Enter async context manager for client usage.

        Parameters
        ----------
        None
            This method takes no parameters.

        Returns
        -------
        VFarmAsyncApiClient
            Current async client instance.

        Examples
        --------
        .. code-block:: python

           async with VFarmAsyncApiClient(base_url="http://localhost:8003", api_key="...") as client:
               print(client.base_url)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Exit async context manager and close owned HTTP resources.

        Parameters
        ----------
        exc_type:
            Exception type if raised inside context.
        exc:
            Exception instance if raised inside context.
        tb:
            Traceback object if raised inside context.

        Returns
        -------
        None
            Ensures resource cleanup.

        Examples
        --------
        .. code-block:: python

           async with VFarmAsyncApiClient(base_url="http://localhost:8003", api_key="..."):
               pass

        Common Errors
        -------------
        - ``N/A`` -> ``None``: No API call is issued.
        """
        await self.aclose()

    async def _request(self, method: str, path: str, *, retry: bool | None = None, **kwargs: Any) -> Any:
        """
        Execute an async HTTP request with retry and SDK error translation.

        Parameters
        ----------
        method:
            HTTP method.
        path:
            API path relative to ``base_url``.
        retry:
            Optional per-call retry override.
        **kwargs:
            Extra ``httpx`` request keyword arguments.

        Returns
        -------
        Any
            Parsed JSON payload, text payload, or ``None`` for ``204`` responses.

        Examples
        --------
        .. code-block:: python

           payload = await client._request("GET", "/api/v1/health")
           print(payload)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Request validation failed.
        - ``401`` -> ``AuthenticationError``: Invalid credentials.
        - ``404`` -> ``NotFoundError``: Resource not found.
        - ``409`` -> ``ConflictError``: Resource conflict.
        - ``429/5xx`` -> ``VFarmApiError``: Retries exhausted or non-mapped failures.
        """
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
        """
        Decide if retries are enabled for an async HTTP method.

        Parameters
        ----------
        method:
            HTTP method.
        retry_override:
            Per-call retry override.

        Returns
        -------
        bool
            ``True`` when retries should run.

        Examples
        --------
        .. code-block:: python

           should = client._should_retry_method("POST", True)
           print(should)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        if retry_override is not None:
            return retry_override
        if not self.retry_policy.enabled:
            return False
        if method in self.retry_policy.retryable_methods:
            return True
        return self.retry_policy.allow_unsafe_retries

    def _should_retry_status(self, status_code: int) -> bool:
        """
        Decide if an async response status code is retryable.

        Parameters
        ----------
        status_code:
            HTTP response status code.

        Returns
        -------
        bool
            ``True`` when code is configured as retryable.

        Examples
        --------
        .. code-block:: python

           print(client._should_retry_status(429))

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        return status_code in self.retry_policy.retryable_status_codes

    def _compute_backoff_delay(self, retry_attempt: int) -> float:
        """
        Compute exponential backoff delay (with optional jitter) for async retries.

        Parameters
        ----------
        retry_attempt:
            One-based retry attempt number.

        Returns
        -------
        float
            Delay in seconds.

        Examples
        --------
        .. code-block:: python

           delay = client._compute_backoff_delay(3)
           print(delay)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure policy helper.
        """
        delay = min(self.retry_policy.max_delay_s, self.retry_policy.base_delay_s * (2 ** (retry_attempt - 1)))
        if self.retry_policy.jitter == "full":
            return random.uniform(0.0, delay)
        return delay

    def _retry_after_delay(self, response: httpx.Response | None) -> float | None:
        """
        Parse and clamp ``Retry-After`` delay for async retries.

        Parameters
        ----------
        response:
            HTTP response potentially containing ``Retry-After``.

        Returns
        -------
        float | None
            Delay seconds if usable, otherwise ``None``.

        Examples
        --------
        .. code-block:: python

           delay = client._retry_after_delay(response)
           print(delay)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Parsing failures are handled internally.
        """
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
        """
        Await for computed retry delay before another async attempt.

        Parameters
        ----------
        retry_attempt:
            One-based retry attempt number.
        response:
            Last response used for ``Retry-After`` parsing.

        Returns
        -------
        None
            Pauses coroutine execution for retry backoff.

        Examples
        --------
        .. code-block:: python

           await client._sleep_before_retry(1, None)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Delay computation handles missing headers safely.
        """
        delay = self._retry_after_delay(response)
        if delay is None:
            delay = self._compute_backoff_delay(retry_attempt)
        await asyncio.sleep(delay)
