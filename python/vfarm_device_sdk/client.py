from __future__ import annotations

from .alerts import AlertsApiMixin
from .capabilities import CapabilitiesApiMixin
from .capability_groups import CapabilityGroupsApiMixin
from .automation import AutomationApiMixin
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
    AlertsApiMixin,
    AutomationApiMixin,
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
    """
    Synchronous facade client composed from focused API mixins.

    Examples
    --------
    .. code-block:: python

       from vfarm_device_sdk import VFarmClient

       with VFarmClient(base_url="http://localhost:8003", api_key="...") as client:
           health = client.health()
           print(health["status"])

    Common Errors
    -------------
    - ``401`` -> ``AuthenticationError``: Invalid farm API key on API calls.
    - ``400/422`` -> ``ValidationError``: Invalid request payload/parameters on API calls.
    - ``404`` -> ``NotFoundError``: Requested resource does not exist.
    - ``409`` -> ``ConflictError``: Resource conflict on create/upsert paths.
    - ``5xx`` -> ``VFarmApiError``: Server-side failure or transport failure.
    """
