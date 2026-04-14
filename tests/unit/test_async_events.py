from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from vfarm_device_sdk.async_events import AsyncDeviceEventsApiMixin


def _run(coro):
    return asyncio.run(coro)


class _AsyncEventsHarness(AsyncDeviceEventsApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        offset = int(kwargs["params"]["offset"])
        limit = int(kwargs["params"]["limit"])
        total = 3
        now = datetime.now(timezone.utc).isoformat()

        all_events = [
            {
                "id": 1,
                "device_id": "dev-1",
                "event_type": "command_created",
                "event_category": "command",
                "severity": "info",
                "occurred_at": now,
            },
            {
                "id": 2,
                "device_id": "dev-1",
                "event_type": "command_acknowledged",
                "event_category": "command",
                "severity": "info",
                "occurred_at": now,
            },
            {
                "id": 3,
                "device_id": "dev-1",
                "event_type": "command_completed",
                "event_category": "command",
                "severity": "info",
                "occurred_at": now,
            },
        ]
        return {"device_id": "dev-1", "events": all_events[offset : offset + limit], "total": total}


def test_async_get_device_events_and_latest() -> None:
    sdk = _AsyncEventsHarness()
    page = _run(sdk.get_device_events("dev-1", limit=2, offset=0))
    assert page.device_id == "dev-1"
    assert len(page.events) == 2

    latest = _run(sdk.get_latest_device_event("dev-1"))
    assert latest is not None
    assert latest.device_id == "dev-1"


def test_async_iter_device_events_paginates() -> None:
    sdk = _AsyncEventsHarness()

    async def collect_ids() -> list[int]:
        ids: list[int] = []
        async for ev in sdk.iter_device_events("dev-1", page_size=2):
            ids.append(ev.id)
        return ids

    ids = _run(collect_ids())
    assert ids == [1, 2, 3]
