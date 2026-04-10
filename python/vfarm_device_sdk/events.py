from __future__ import annotations

from collections.abc import Iterator

from .models import DeviceEventResponse, DeviceEventsListResponse


class DeviceEventsApiMixin:
    def get_device_events(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DeviceEventsListResponse:
        params: dict[str, object] = {
            "limit": limit,
            "offset": offset,
        }
        if event_type is not None:
            params["event_type"] = event_type
        if severity is not None:
            params["severity"] = severity

        data = self._request("GET", f"/api/v1/devices/{device_id}/events", params=params)
        return DeviceEventsListResponse.model_validate(data)

    def iter_device_events(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        page_size: int = 100,
    ) -> Iterator[DeviceEventResponse]:
        offset = 0
        while True:
            page = self.get_device_events(
                device_id,
                event_type=event_type,
                severity=severity,
                limit=page_size,
                offset=offset,
            )
            for event in page.events:
                yield event
            offset += len(page.events)
            if offset >= page.total or not page.events:
                break

    def get_latest_device_event(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
    ) -> DeviceEventResponse | None:
        page = self.get_device_events(
            device_id,
            event_type=event_type,
            severity=severity,
            limit=1,
            offset=0,
        )
        if not page.events:
            return None
        return page.events[0]
