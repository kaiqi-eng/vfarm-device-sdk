from __future__ import annotations

from .commands import CommandApiMixin
from .core import VFarmApiClient
from .devices import DeviceApiMixin
from .ingestion import IngestionApiMixin


class VFarmClient(CommandApiMixin, DeviceApiMixin, IngestionApiMixin, VFarmApiClient):
    """Facade client composed from focused API mixins."""
