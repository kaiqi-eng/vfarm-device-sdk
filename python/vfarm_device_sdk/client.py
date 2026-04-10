from __future__ import annotations

from .commands import CommandApiMixin
from .core import VFarmApiClient
from .devices import DeviceApiMixin
from .events import DeviceEventsApiMixin
from .farms import FarmApiMixin
from .ingestion import IngestionApiMixin
from .readings import ReadingsApiMixin
from .thresholds import DeviceThresholdsApiMixin


class VFarmClient(
    CommandApiMixin,
    DeviceApiMixin,
    DeviceEventsApiMixin,
    DeviceThresholdsApiMixin,
    FarmApiMixin,
    IngestionApiMixin,
    ReadingsApiMixin,
    VFarmApiClient,
):
    """Facade client composed from focused API mixins."""
