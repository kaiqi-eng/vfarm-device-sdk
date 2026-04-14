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


class AsyncReadingsApiMixin:
    async def get_latest_reading(self, sensor_id: str) -> LatestReadingResponse:
        data = await self._request("GET", "/api/v1/readings/latest", params={"sensor_id": sensor_id})
        return LatestReadingResponse.model_validate(data)

    async def list_readings(
        self,
        sensor_id: str,
        *,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
        status: str | None = None,
    ) -> ReadingsListResponse:
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

        data = await self._request("GET", "/api/v1/readings", params=params)
        return ReadingsListResponse.model_validate(data)

    async def get_reading_stats(self, sensor_id: str, *, window: StatsWindow = "24h") -> ReadingStatsResponse:
        data = await self._request("GET", "/api/v1/readings/stats", params={"sensor_id": sensor_id, "window": window})
        return ReadingStatsResponse.model_validate(data)

    async def get_readings_analytics(
        self,
        sensor_id: str,
        *,
        window: StatsWindow = "24h",
        recent_limit: int = 100,
    ) -> ReadingAnalyticsSnapshot:
        try:
            latest = await self.get_latest_reading(sensor_id)
        except NotFoundError:
            latest = None

        recent = await self.list_readings(sensor_id, limit=recent_limit)
        stats = await self.get_reading_stats(sensor_id, window=window)

        return ReadingAnalyticsSnapshot(
            sensor_id=sensor_id,
            latest=latest,
            recent=recent,
            stats=stats,
        )
