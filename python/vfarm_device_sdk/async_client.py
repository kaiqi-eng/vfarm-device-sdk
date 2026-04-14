from __future__ import annotations

from .async_commands import AsyncCommandApiMixin
from .async_devices import AsyncDeviceApiMixin
from .async_events import AsyncDeviceEventsApiMixin
from .async_farms import AsyncFarmApiMixin
from .async_ingestion import AsyncIngestionApiMixin
from .async_readings import AsyncReadingsApiMixin
from .core import VFarmAsyncApiClient


class AsyncVFarmClient(
    AsyncCommandApiMixin,
    AsyncDeviceApiMixin,
    AsyncDeviceEventsApiMixin,
    AsyncFarmApiMixin,
    AsyncIngestionApiMixin,
    AsyncReadingsApiMixin,
    VFarmAsyncApiClient,
):
    """Async facade client for device, command, events, farms, ingestion, and readings APIs."""
