from __future__ import annotations

from .async_commands import AsyncCommandApiMixin
from .async_devices import AsyncDeviceApiMixin
from .core import VFarmAsyncApiClient


class AsyncVFarmClient(
    AsyncCommandApiMixin,
    AsyncDeviceApiMixin,
    VFarmAsyncApiClient,
):
    """Async facade client for device and command APIs."""
