from __future__ import annotations

from .capabilities import CapabilitiesApiMixin
from .capability_groups import CapabilityGroupsApiMixin
from .commands import CommandApiMixin
from .core import VFarmApiClient
from .device_capabilities import DeviceCapabilitiesApiMixin
from .devices import DeviceApiMixin
from .events import DeviceEventsApiMixin
from .farms import FarmApiMixin
from .ingestion import IngestionApiMixin
from .readings import ReadingsApiMixin
from .sensor_types import SensorTypeApiMixin
from .thresholds import DeviceThresholdsApiMixin


class VFarmClient(
    CapabilitiesApiMixin,
    CapabilityGroupsApiMixin,
    CommandApiMixin,
    DeviceCapabilitiesApiMixin,
    DeviceApiMixin,
    DeviceEventsApiMixin,
    DeviceThresholdsApiMixin,
    FarmApiMixin,
    IngestionApiMixin,
    ReadingsApiMixin,
    SensorTypeApiMixin,
    VFarmApiClient,
):
    """Facade client composed from focused API mixins."""
