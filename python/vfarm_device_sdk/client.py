from __future__ import annotations

from .commands import CommandApiMixin
from .core import VFarmApiClient
from .devices import DeviceApiMixin
from .farms import FarmApiMixin
from .ingestion import IngestionApiMixin
from .readings import ReadingsApiMixin


class VFarmClient(CommandApiMixin, DeviceApiMixin, FarmApiMixin, IngestionApiMixin, ReadingsApiMixin, VFarmApiClient):
    """Facade client composed from focused API mixins."""
