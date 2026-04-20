from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    DeviceBatchCreateItem,
    DeviceBatchRegisterResponse,
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceHeartbeatResponse,
    DeviceListResponse,
    DeviceMetadataResponse,
    DeviceMetadataUpdateResponse,
    DeviceResponse,
    DeviceUpdate,
    EnsureDeviceResult,
)


class AsyncDeviceApiMixin:
    async def register_device(self, payload: DeviceCreate) -> DeviceCreatedResponse:
        """
        Register a new device.

        Parameters
        ----------
        payload:
            Device creation payload.

        Returns
        -------
        DeviceCreatedResponse
            Created device metadata from the API.

        Examples
        --------
        .. code-block:: python

           created = await client.register_device(DeviceCreate(id="sensor-001", farm_id="farm-a", device_type="sensor"))
           print(created.device_id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid device payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Device ID already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("POST", "/api/v1/devices", json=payload.model_dump(mode="json", exclude_none=True))
        return DeviceCreatedResponse.model_validate(data)

    async def get_device(self, device_id: str) -> DeviceResponse:
        """
        Fetch one device by ID.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        DeviceResponse
            Current device record.

        Examples
        --------
        .. code-block:: python

           device = await client.get_device("sensor-001")
           print(device.id, device.status)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}")
        return DeviceResponse.model_validate(data)

    async def list_devices(
        self,
        *,
        farm_id: str | None = None,
        status: str | None = None,
        device_type: str | None = None,
        health_below: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DeviceListResponse:
        """
        List devices with optional filters and pagination.

        Parameters
        ----------
        farm_id:
            Filter by farm ID.
        status:
            Filter by device status.
        device_type:
            Filter by device type.
        health_below:
            Filter by health score threshold.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        DeviceListResponse
            Paged list of devices.

        Examples
        --------
        .. code-block:: python

           page = await client.list_devices(farm_id="farm-a", limit=50, offset=0)
           print(page.total, len(page.devices))

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid filter values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "farm_id": farm_id,
            "status": status,
            "device_type": device_type,
            "health_below": health_below,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/devices", params={k: v for k, v in params.items() if v is not None})
        return DeviceListResponse.model_validate(data)

    async def list_offline_devices(self, *, limit: int = 100) -> DeviceListResponse:
        """
        List devices currently considered offline.

        Parameters
        ----------
        limit:
            Max devices to return.

        Returns
        -------
        DeviceListResponse
            Paged offline-device list.

        Examples
        --------
        .. code-block:: python

           offline = await client.list_offline_devices(limit=25)
           print(offline.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid limit.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", "/api/v1/devices/offline", params={"limit": limit})
        return DeviceListResponse.model_validate(data)

    async def list_unhealthy_devices(self, *, threshold: int = 80, limit: int = 100) -> DeviceListResponse:
        """
        List devices below a health threshold.

        Parameters
        ----------
        threshold:
            Health threshold (inclusive cutoff defined by backend).
        limit:
            Max devices to return.

        Returns
        -------
        DeviceListResponse
            Paged unhealthy-device list.

        Examples
        --------
        .. code-block:: python

           bad = await client.list_unhealthy_devices(threshold=70, limit=20)
           print(bad.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid threshold/limit.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", "/api/v1/devices/unhealthy", params={"threshold": threshold, "limit": limit})
        return DeviceListResponse.model_validate(data)

    async def update_device(self, device_id: str, payload: DeviceUpdate) -> DeviceResponse:
        """
        Patch mutable fields on a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        payload:
            Partial update payload.

        Returns
        -------
        DeviceResponse
            Updated device record.

        Examples
        --------
        .. code-block:: python

           updated = await client.update_device("sensor-001", DeviceUpdate(notes="Moved to rack-b"))
           print(updated.notes)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/devices/{quote(device_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceResponse.model_validate(data)

    async def delete_device(self, device_id: str) -> None:
        """
        Delete a device by ID.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        None
            Returns ``None`` when deletion succeeds.

        Examples
        --------
        .. code-block:: python

           await client.delete_device("sensor-001")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/devices/{quote(device_id, safe='')}")

    async def send_device_heartbeat(self, device_id: str) -> DeviceHeartbeatResponse:
        """
        Submit a heartbeat for a device.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        DeviceHeartbeatResponse
            Heartbeat acknowledgement payload.

        Examples
        --------
        .. code-block:: python

           hb = await client.send_device_heartbeat("sensor-001")
           print(hb.status)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("POST", f"/api/v1/devices/{quote(device_id, safe='')}/heartbeat")
        return DeviceHeartbeatResponse.model_validate(data)

    async def register_devices_batch(self, devices: list[DeviceBatchCreateItem]) -> DeviceBatchRegisterResponse:
        """
        Register multiple devices in one request.

        Parameters
        ----------
        devices:
            Device payload list.

        Returns
        -------
        DeviceBatchRegisterResponse
            Batch creation result.

        Examples
        --------
        .. code-block:: python

           result = await client.register_devices_batch([DeviceBatchCreateItem(id="sensor-002", farm_id="farm-a", device_type="sensor")])
           print(result.created_count)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid batch payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: At least one device conflicts.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        payload = {"devices": [d.model_dump(mode="json", exclude_none=True) for d in devices]}
        data = await self._request("POST", "/api/v1/devices/batch", json=payload)
        return DeviceBatchRegisterResponse.model_validate(data)

    async def get_device_metadata(self, device_id: str) -> DeviceMetadataResponse:
        """
        Retrieve metadata for a device.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        DeviceMetadataResponse
            Metadata record.

        Examples
        --------
        .. code-block:: python

           meta = await client.get_device_metadata("sensor-001")
           print(meta.metadata)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}/metadata")
        return DeviceMetadataResponse.model_validate(data)

    async def update_device_metadata(self, device_id: str, metadata: dict[str, object]) -> DeviceMetadataUpdateResponse:
        """
        Patch metadata for a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        metadata:
            Arbitrary metadata mapping.

        Returns
        -------
        DeviceMetadataUpdateResponse
            Updated metadata response.

        Examples
        --------
        .. code-block:: python

           result = await client.update_device_metadata("sensor-001", {"zone": "north"})
           print(result.updated)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid metadata payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device does not exist.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("PATCH", f"/api/v1/devices/{quote(device_id, safe='')}/metadata", json=metadata)
        return DeviceMetadataUpdateResponse.model_validate(data)

    async def ensure_device(self, payload: DeviceCreate) -> EnsureDeviceResult:
        """
        Ensure a device exists, creating it when missing.

        Parameters
        ----------
        payload:
            Device creation payload.

        Returns
        -------
        EnsureDeviceResult
            Wrapper indicating whether the device was newly created.

        Examples
        --------
        .. code-block:: python

           ensured = await client.ensure_device(DeviceCreate(id="sensor-001", farm_id="farm-a", device_type="sensor"))
           print(ensured.created, ensured.device.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid device payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Follow-up read could not find the device.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            created = await self.register_device(payload)
            device = await self.get_device(payload.id)
            return EnsureDeviceResult(created=True, device=device, created_response=created)
        except ConflictError:
            device = await self.get_device(payload.id)
            return EnsureDeviceResult(created=False, device=device)
