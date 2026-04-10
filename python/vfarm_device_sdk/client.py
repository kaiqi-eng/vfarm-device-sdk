from __future__ import annotations

from .commands import CommandApiMixin
from .core import VFarmApiClient
from .device_capabilities import DeviceCapabilitiesApiMixin
from .devices import DeviceApiMixin
from .events import DeviceEventsApiMixin
from .farms import FarmApiMixin
from .ingestion import IngestionApiMixin
from .readings import ReadingsApiMixin
from .thresholds import DeviceThresholdsApiMixin


class VFarmClient(
    CommandApiMixin,
    DeviceCapabilitiesApiMixin,
    DeviceApiMixin,
    DeviceEventsApiMixin,
    DeviceThresholdsApiMixin,
    FarmApiMixin,
    IngestionApiMixin,
    ReadingsApiMixin,
    VFarmApiClient,
):
    """Facade client composed from focused API mixins."""
