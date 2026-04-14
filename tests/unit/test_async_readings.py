from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from vfarm_device_sdk.async_readings import AsyncReadingsApiMixin
from vfarm_device_sdk.exceptions import NotFoundError


def _run(coro):
    return asyncio.run(coro)


class _AsyncReadingsHarness(AsyncReadingsApiMixin):
    def __init__(self, *, latest_not_found: bool = False) -> None:
        self.latest_not_found = latest_not_found
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc)
        if path == "/api/v1/readings/latest":
            if self.latest_not_found:
                raise NotFoundError("no latest", status_code=404)
            return {
                "id": 1,
                "sensor_id": kwargs["params"]["sensor_id"],
                "reading_ts": now.isoformat(),
                "received_at": now.isoformat(),
                "temperature_c": 24.0,
                "temperature_status": "ok",
                "humidity_rh": 58.0,
                "humidity_status": "ok",
                "firmware": "1.0.0",
            }
        if path == "/api/v1/readings":
            from_time = now - timedelta(minutes=10)
            return {
                "sensor_id": kwargs["params"]["sensor_id"],
                "from": from_time.isoformat(),
                "to": now.isoformat(),
                "count": 1,
                "readings": [
                    {
                        "id": 1,
                        "sensor_id": kwargs["params"]["sensor_id"],
                        "reading_ts": now.isoformat(),
                        "received_at": now.isoformat(),
                        "temperature_c": 24.0,
                        "temperature_status": "ok",
                        "humidity_rh": 58.0,
                        "humidity_status": "ok",
                        "firmware": "1.0.0",
                    }
                ],
            }
        if path == "/api/v1/readings/stats":
            return {
                "sensor_id": kwargs["params"]["sensor_id"],
                "window": kwargs["params"]["window"],
                "from": (now - timedelta(hours=1)).isoformat(),
                "to": now.isoformat(),
                "temperature": {"min_c": 23.0, "max_c": 25.0, "avg_c": 24.0},
                "humidity": {"min_rh": 57.0, "max_rh": 59.0, "avg_rh": 58.0},
                "total_readings": 1,
                "error_readings": 0,
            }
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_readings_methods() -> None:
    sdk = _AsyncReadingsHarness()
    latest = _run(sdk.get_latest_reading("sensor-1"))
    assert latest.sensor_id == "sensor-1"

    readings = _run(sdk.list_readings("sensor-1", limit=10))
    assert readings.sensor_id == "sensor-1"
    assert readings.count == 1

    stats = _run(sdk.get_reading_stats("sensor-1", window="1h"))
    assert stats.sensor_id == "sensor-1"
    assert stats.window == "1h"


def test_async_get_readings_analytics_handles_missing_latest() -> None:
    sdk = _AsyncReadingsHarness(latest_not_found=True)
    snapshot = _run(sdk.get_readings_analytics("sensor-2", window="1h", recent_limit=5))
    assert snapshot.sensor_id == "sensor-2"
    assert snapshot.latest is None
    assert snapshot.recent.count == 1
    assert snapshot.stats.total_readings == 1
