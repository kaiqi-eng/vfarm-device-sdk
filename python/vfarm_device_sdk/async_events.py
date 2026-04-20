from __future__ import annotations

from collections.abc import AsyncIterator

from .models import DeviceEventResponse, DeviceEventsListResponse


class AsyncDeviceEventsApiMixin:
    async def get_device_events(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DeviceEventsListResponse:
        """
        Fetch a page of events for a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        event_type:
            Optional event-type filter.
        severity:
            Optional severity filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        DeviceEventsListResponse
            Paged device event payload.

        Examples
        --------
        .. code-block:: python

           page = await client.get_device_events("sensor-001", severity="warning", limit=20)
           print(page.total, len(page.events))

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid filters or pagination.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params: dict[str, object] = {
            "limit": limit,
            "offset": offset,
        }
        if event_type is not None:
            params["event_type"] = event_type
        if severity is not None:
            params["severity"] = severity

        data = await self._request("GET", f"/api/v1/devices/{device_id}/events", params=params)
        return DeviceEventsListResponse.model_validate(data)

    async def iter_device_events(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[DeviceEventResponse]:
        """
        Iterate all device events using automatic pagination.

        Parameters
        ----------
        device_id:
            Device identifier.
        event_type:
            Optional event-type filter.
        severity:
            Optional severity filter.
        page_size:
            Page size for each API request.

        Returns
        -------
        AsyncIterator[DeviceEventResponse]
            Event stream iterator.

        Examples
        --------
        .. code-block:: python

           async for event in client.iter_device_events("sensor-001", page_size=50):
               print(event.event_type)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid filters or pagination.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = await self.get_device_events(
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

    async def get_latest_device_event(
        self,
        device_id: str,
        *,
        event_type: str | None = None,
        severity: str | None = None,
    ) -> DeviceEventResponse | None:
        """
        Return the latest event for a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        event_type:
            Optional event-type filter.
        severity:
            Optional severity filter.

        Returns
        -------
        DeviceEventResponse | None
            Latest matching event or ``None`` if no events exist.

        Examples
        --------
        .. code-block:: python

           latest = await client.get_latest_device_event("sensor-001")
           print(latest.event_type if latest else "no events")

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid filters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        page = await self.get_device_events(
            device_id,
            event_type=event_type,
            severity=severity,
            limit=1,
            offset=0,
        )
        if not page.events:
            return None
        return page.events[0]
