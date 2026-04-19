from __future__ import annotations

from .exceptions import ConflictError
from .models import (
    DeviceThresholdCreate,
    DeviceThresholdListResponse,
    DeviceThresholdResponse,
    DeviceThresholdUpdate,
)


class DeviceThresholdsApiMixin:
    def list_device_thresholds(self, device_id: str) -> DeviceThresholdListResponse:
        """
        List all thresholds configured for a device.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        DeviceThresholdListResponse
            Threshold collection.

        Examples
        --------
        .. code-block:: python

           thresholds = client.list_device_thresholds("sensor-001")
           print(thresholds.total)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/devices/{device_id}/thresholds")
        return DeviceThresholdListResponse.model_validate(data)

    def get_device_threshold(self, device_id: str, metric: str) -> DeviceThresholdResponse:
        """
        Get one threshold for a specific metric.

        Parameters
        ----------
        device_id:
            Device identifier.
        metric:
            Metric key, such as ``temperature``.

        Returns
        -------
        DeviceThresholdResponse
            Matching threshold record.

        Examples
        --------
        .. code-block:: python

           threshold = client.get_device_threshold("sensor-001", "temperature")
           print(threshold.max_value)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/metric threshold not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/devices/{device_id}/thresholds/{metric}")
        return DeviceThresholdResponse.model_validate(data)

    def create_device_threshold(self, device_id: str, payload: DeviceThresholdCreate) -> DeviceThresholdResponse:
        """
        Create a threshold for a device metric.

        Parameters
        ----------
        device_id:
            Device identifier.
        payload:
            Threshold creation payload.

        Returns
        -------
        DeviceThresholdResponse
            Created threshold.

        Examples
        --------
        .. code-block:: python

           created = client.create_device_threshold("sensor-001", DeviceThresholdCreate(metric="temperature", max_value=30))
           print(created.metric)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid threshold payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``409`` -> ``ConflictError``: Threshold already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "POST",
            f"/api/v1/devices/{device_id}/thresholds",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceThresholdResponse.model_validate(data)

    def update_device_threshold(
        self,
        device_id: str,
        metric: str,
        payload: DeviceThresholdUpdate,
    ) -> DeviceThresholdResponse:
        """
        Update an existing threshold.

        Parameters
        ----------
        device_id:
            Device identifier.
        metric:
            Metric key to update.
        payload:
            Partial threshold update payload.

        Returns
        -------
        DeviceThresholdResponse
            Updated threshold.

        Examples
        --------
        .. code-block:: python

           updated = client.update_device_threshold("sensor-001", "temperature", DeviceThresholdUpdate(max_value=31))
           print(updated.max_value)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid threshold update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Threshold not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "PATCH",
            f"/api/v1/devices/{device_id}/thresholds/{metric}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceThresholdResponse.model_validate(data)

    def delete_device_threshold(self, device_id: str, metric: str) -> None:
        """
        Delete a threshold for a metric.

        Parameters
        ----------
        device_id:
            Device identifier.
        metric:
            Metric key.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           client.delete_device_threshold("sensor-001", "temperature")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Threshold not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        self._request("DELETE", f"/api/v1/devices/{device_id}/thresholds/{metric}")

    def set_metric_limits(
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
        """
        Upsert threshold limits for a generic metric.

        Parameters
        ----------
        device_id:
            Device identifier.
        metric:
            Metric key to configure.
        min_value:
            Optional lower bound.
        max_value:
            Optional upper bound.
        severity:
            Alert severity label.
        cooldown_minutes:
            Cooldown duration.
        enabled:
            Whether the rule is active.

        Returns
        -------
        DeviceThresholdResponse
            Created or updated threshold.

        Examples
        --------
        .. code-block:: python

           threshold = client.set_metric_limits("sensor-001", metric="temperature", min_value=18, max_value=30)
           print(threshold.metric, threshold.enabled)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid threshold values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            return self.create_device_threshold(
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
            return self.update_device_threshold(
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

    def set_temperature_limits(
        self,
        device_id: str,
        *,
        min_c: float | None = None,
        max_c: float | None = None,
        severity: str = "warning",
        cooldown_minutes: int = 15,
        enabled: bool = True,
    ) -> DeviceThresholdResponse:
        """
        Upsert temperature threshold limits.

        Parameters
        ----------
        device_id:
            Device identifier.
        min_c:
            Optional minimum temperature in celsius.
        max_c:
            Optional maximum temperature in celsius.
        severity:
            Alert severity label.
        cooldown_minutes:
            Cooldown duration.
        enabled:
            Whether the rule is active.

        Returns
        -------
        DeviceThresholdResponse
            Created or updated temperature threshold.

        Examples
        --------
        .. code-block:: python

           threshold = client.set_temperature_limits("sensor-001", min_c=18, max_c=30)
           print(threshold.metric, threshold.max_value)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid threshold values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.set_metric_limits(
            device_id,
            metric="temperature",
            min_value=min_c,
            max_value=max_c,
            severity=severity,
            cooldown_minutes=cooldown_minutes,
            enabled=enabled,
        )
