from __future__ import annotations

from .async_alerts import AsyncAlertsApiMixin
from .async_automation import AsyncAutomationApiMixin
from .async_capability_groups import AsyncCapabilityGroupsApiMixin
from .async_capabilities import AsyncCapabilitiesApiMixin
from .async_commands import AsyncCommandApiMixin
from .async_device_capabilities import AsyncDeviceCapabilitiesApiMixin
from .async_devices import AsyncDeviceApiMixin
from .async_events import AsyncDeviceEventsApiMixin
from .async_farms import AsyncFarmApiMixin
from .async_ingestion import AsyncIngestionApiMixin
from .async_readings import AsyncReadingsApiMixin
from .async_sensor_types import AsyncSensorTypeApiMixin
from .async_thresholds import AsyncDeviceThresholdsApiMixin
from .core import VFarmAsyncApiClient


class AsyncVFarmClient(
    AsyncAlertsApiMixin,
    AsyncAutomationApiMixin,
    AsyncCapabilityGroupsApiMixin,
    AsyncCapabilitiesApiMixin,
    AsyncCommandApiMixin,
    AsyncDeviceCapabilitiesApiMixin,
    AsyncDeviceApiMixin,
    AsyncDeviceEventsApiMixin,
    AsyncFarmApiMixin,
    AsyncIngestionApiMixin,
    AsyncReadingsApiMixin,
    AsyncSensorTypeApiMixin,
    AsyncDeviceThresholdsApiMixin,
    VFarmAsyncApiClient,
):
    """Async facade client for alerts, automation, capability groups, capabilities, device, command, device capabilities, events, farms, ingestion, readings, sensor type, and thresholds APIs."""
