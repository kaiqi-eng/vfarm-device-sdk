from __future__ import annotations

from datetime import datetime

from .exceptions import NotFoundError
from .models import (
    LatestReadingResponse,
    ReadingAnalyticsSnapshot,
    ReadingStatsResponse,
    ReadingsListResponse,
    StatsWindow,
)


class ReadingsApiMixin:
    def get_latest_reading(self, sensor_id: str) -> LatestReadingResponse:
        """
        Get the latest reading for a sensor.

        Parameters
        ----------
        sensor_id:
            Sensor identifier.

        Returns
        -------
        LatestReadingResponse
            Latest sensor reading.

        Examples
        --------
        .. code-block:: python

           latest = client.get_latest_reading("sensor-001")
           print(latest.id, latest.sensor_id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: No reading exists for sensor.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", "/api/v1/readings/latest", params={"sensor_id": sensor_id})
        return LatestReadingResponse.model_validate(data)

    def list_readings(
        self,
        sensor_id: str,
        *,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
        status: str | None = None,
    ) -> ReadingsListResponse:
        """
        List historical readings for a sensor.

        Parameters
        ----------
        sensor_id:
            Sensor identifier.
        from_time:
            Optional lower time bound.
        to_time:
            Optional upper time bound.
        limit:
            Max records to return.
        status:
            Optional reading status filter.

        Returns
        -------
        ReadingsListResponse
            Historical readings page.

        Examples
        --------
        .. code-block:: python

           history = client.list_readings("sensor-001", limit=50)
           print(history.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Sensor not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params: dict[str, object] = {
            "sensor_id": sensor_id,
            "limit": limit,
        }
        if from_time is not None:
            params["from"] = from_time.isoformat()
        if to_time is not None:
            params["to"] = to_time.isoformat()
        if status is not None:
            params["status"] = status

        data = self._request("GET", "/api/v1/readings", params=params)
        return ReadingsListResponse.model_validate(data)

    def get_reading_stats(self, sensor_id: str, *, window: StatsWindow = "24h") -> ReadingStatsResponse:
        """
        Get aggregated reading statistics for a time window.

        Parameters
        ----------
        sensor_id:
            Sensor identifier.
        window:
            Stats window label.

        Returns
        -------
        ReadingStatsResponse
            Aggregated statistics payload.

        Examples
        --------
        .. code-block:: python

           stats = client.get_reading_stats("sensor-001", window="24h")
           print(stats.total_readings)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid window value.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Sensor not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", "/api/v1/readings/stats", params={"sensor_id": sensor_id, "window": window})
        return ReadingStatsResponse.model_validate(data)

    def get_readings_analytics(
        self,
        sensor_id: str,
        *,
        window: StatsWindow = "24h",
        recent_limit: int = 100,
    ) -> ReadingAnalyticsSnapshot:
        """
        Build a combined analytics snapshot from latest, recent, and stats queries.

        Parameters
        ----------
        sensor_id:
            Sensor identifier.
        window:
            Stats window label.
        recent_limit:
            Max records requested for recent history.

        Returns
        -------
        ReadingAnalyticsSnapshot
            Combined analytics view.

        Examples
        --------
        .. code-block:: python

           snapshot = client.get_readings_analytics("sensor-001", window="24h", recent_limit=100)
           print(snapshot.sensor_id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Raised when stats/recent endpoints fail for missing sensor.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            latest = self.get_latest_reading(sensor_id)
        except NotFoundError:
            latest = None

        recent = self.list_readings(sensor_id, limit=recent_limit)
        stats = self.get_reading_stats(sensor_id, window=window)

        return ReadingAnalyticsSnapshot(
            sensor_id=sensor_id,
            latest=latest,
            recent=recent,
            stats=stats,
        )
