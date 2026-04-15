from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_thresholds import AsyncDeviceThresholdsApiMixin
from vfarm_device_sdk.exceptions import ConflictError
from vfarm_device_sdk.models import DeviceThresholdCreate


def _run(coro):
    return asyncio.run(coro)


class _AsyncThresholdHarness(AsyncDeviceThresholdsApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.create_conflict = False

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        now = datetime.now(timezone.utc).isoformat()

        if method == "POST" and path.endswith("/thresholds"):
            if self.create_conflict:
                raise ConflictError("exists", status_code=409)
            body = kwargs["json"]
            return {
                "id": "t-1",
                "device_id": "dev-1",
                "metric": body["metric"],
                "min_value": body.get("min_value"),
                "max_value": body.get("max_value"),
                "severity": body.get("severity", "warning"),
                "cooldown_minutes": body.get("cooldown_minutes", 15),
                "enabled": body.get("enabled", True),
                "created_at": now,
                "updated_at": now,
            }
        if method == "PATCH" and "/thresholds/" in path:
            body = kwargs["json"]
            metric = path.rsplit("/", 1)[-1]
            return {
                "id": "t-1",
                "device_id": "dev-1",
                "metric": metric,
                "min_value": body.get("min_value"),
                "max_value": body.get("max_value"),
                "severity": body.get("severity", "warning"),
                "cooldown_minutes": body.get("cooldown_minutes", 15),
                "enabled": body.get("enabled", True),
                "created_at": now,
                "updated_at": now,
            }
        if method == "GET" and path.endswith("/thresholds"):
            return {"device_id": "dev-1", "thresholds": [], "total": 0}
        if method == "GET" and "/thresholds/" in path:
            metric = path.rsplit("/", 1)[-1]
            return {
                "id": "t-1",
                "device_id": "dev-1",
                "metric": metric,
                "min_value": 10.0,
                "max_value": 20.0,
                "severity": "warning",
                "cooldown_minutes": 15,
                "enabled": True,
                "created_at": now,
                "updated_at": now,
            }
        if method == "DELETE" and "/thresholds/" in path:
            return None
        raise AssertionError(f"Unhandled call: {method} {path}")


def test_async_threshold_crud() -> None:
    sdk = _AsyncThresholdHarness()
    created = _run(
        sdk.create_device_threshold(
            "dev-1",
            DeviceThresholdCreate(metric="temperature", min_value=18.0, max_value=30.0),
        )
    )
    assert created.metric == "temperature"
    fetched = _run(sdk.get_device_threshold("dev-1", "temperature"))
    assert fetched.metric == "temperature"
    listed = _run(sdk.list_device_thresholds("dev-1"))
    assert listed.device_id == "dev-1"
    _run(sdk.delete_device_threshold("dev-1", "temperature"))


def test_async_set_metric_limits_create_then_update_on_conflict() -> None:
    sdk = _AsyncThresholdHarness()
    created = _run(
        sdk.set_metric_limits(
            "dev-1",
            metric="temperature",
            min_value=18.0,
            max_value=30.0,
        )
    )
    assert created.metric == "temperature"
    assert created.min_value == 18.0

    sdk.create_conflict = True
    updated = _run(
        sdk.set_metric_limits(
            "dev-1",
            metric="temperature",
            min_value=17.0,
            max_value=31.0,
            severity="error",
        )
    )
    assert updated.metric == "temperature"
    assert updated.min_value == 17.0
    assert updated.max_value == 31.0
    assert updated.severity == "error"


def test_async_set_temperature_limits_helper() -> None:
    sdk = _AsyncThresholdHarness()
    out = _run(sdk.set_temperature_limits("dev-1", min_c=16.0, max_c=29.0))
    assert out.metric == "temperature"
    assert out.min_value == 16.0
    assert out.max_value == 29.0
