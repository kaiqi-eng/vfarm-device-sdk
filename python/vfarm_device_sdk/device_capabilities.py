from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    DeviceCapabilityCreate,
    DeviceCapabilityListResponse,
    DeviceCapabilityResponse,
    DeviceCapabilityUpdate,
)


class DeviceCapabilitiesApiMixin:
    def list_device_capabilities(self, device_id: str) -> DeviceCapabilityListResponse:
        """
        List effective capabilities for a device.

        Parameters
        ----------
        device_id:
            Device identifier.

        Returns
        -------
        DeviceCapabilityListResponse
            Capability list with overrides.

        Examples
        --------
        .. code-block:: python

           caps = client.list_device_capabilities("sensor-001")
           print(caps.total)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/devices/{quote(device_id, safe='')}/capabilities")
        return DeviceCapabilityListResponse.model_validate(data)

    def create_device_capability_override(
        self,
        device_id: str,
        payload: DeviceCapabilityCreate,
    ) -> DeviceCapabilityResponse:
        """
        Create a device-specific capability override.

        Parameters
        ----------
        device_id:
            Device identifier.
        payload:
            Capability override payload.

        Returns
        -------
        DeviceCapabilityResponse
            Created override response.

        Examples
        --------
        .. code-block:: python

           created = client.create_device_capability_override("sensor-001", DeviceCapabilityCreate(capability_id="temperature"))
           print(created.capability_id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid capability payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/capability not found.
        - ``409`` -> ``ConflictError``: Override already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "POST",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceCapabilityResponse.model_validate(data)

    def update_device_capability_override(
        self,
        device_id: str,
        capability_id: str,
        payload: DeviceCapabilityUpdate,
    ) -> DeviceCapabilityResponse:
        """
        Update a device capability override.

        Parameters
        ----------
        device_id:
            Device identifier.
        capability_id:
            Capability identifier.
        payload:
            Capability update payload.

        Returns
        -------
        DeviceCapabilityResponse
            Updated override response.

        Examples
        --------
        .. code-block:: python

           updated = client.update_device_capability_override("sensor-001", "temperature", DeviceCapabilityUpdate(calibration_offset=0.1))
           print(updated.calibration_offset)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid capability update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Override not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "PATCH",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return DeviceCapabilityResponse.model_validate(data)

    def delete_device_capability_override(self, device_id: str, capability_id: str) -> None:
        """
        Delete a device capability override.

        Parameters
        ----------
        device_id:
            Device identifier.
        capability_id:
            Capability identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           client.delete_device_capability_override("sensor-001", "temperature")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Override not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        self._request(
            "DELETE",
            f"/api/v1/devices/{quote(device_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    def upsert_device_capability_override(
        self,
        device_id: str,
        *,
        capability_id: str,
        calibration_offset: float = 0.0,
        calibration_scale: float = 1.0,
        custom_min: float | None = None,
        custom_max: float | None = None,
        enabled: bool = True,
        notes: str | None = None,
    ) -> DeviceCapabilityResponse:
        """
        Upsert a device capability override.

        Parameters
        ----------
        device_id:
            Device identifier.
        capability_id:
            Capability identifier.
        calibration_offset:
            Calibration offset value.
        calibration_scale:
            Calibration scale multiplier.
        custom_min:
            Optional custom lower bound.
        custom_max:
            Optional custom upper bound.
        enabled:
            Whether this override is active.
        notes:
            Optional free-form note.

        Returns
        -------
        DeviceCapabilityResponse
            Created or updated override.

        Examples
        --------
        .. code-block:: python

           override = client.upsert_device_capability_override("sensor-001", capability_id="temperature", calibration_offset=0.1)
           print(override.capability_id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid capability values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/capability not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        create_payload = DeviceCapabilityCreate(
            capability_id=capability_id,
            calibration_offset=calibration_offset,
            calibration_scale=calibration_scale,
            custom_min=custom_min,
            custom_max=custom_max,
            enabled=enabled,
            notes=notes,
        )
        try:
            return self.create_device_capability_override(device_id, create_payload)
        except ConflictError:
            return self.update_device_capability_override(
                device_id,
                capability_id,
                DeviceCapabilityUpdate(
                    calibration_offset=calibration_offset,
                    calibration_scale=calibration_scale,
                    custom_min=custom_min,
                    custom_max=custom_max,
                    enabled=enabled,
                    notes=notes,
                ),
            )

    def calibrate_device_capability(
        self,
        device_id: str,
        capability_id: str,
        *,
        offset: float = 0.0,
        scale: float = 1.0,
        notes: str | None = None,
    ) -> DeviceCapabilityResponse:
        """
        Convenience wrapper for calibration-only updates.

        Parameters
        ----------
        device_id:
            Device identifier.
        capability_id:
            Capability identifier.
        offset:
            Calibration offset.
        scale:
            Calibration scale multiplier.
        notes:
            Optional calibration note.

        Returns
        -------
        DeviceCapabilityResponse
            Created or updated override with calibration fields.

        Examples
        --------
        .. code-block:: python

           calibrated = client.calibrate_device_capability("sensor-001", "temperature", offset=0.05, scale=1.0)
           print(calibrated.calibration_offset)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid calibration values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/capability not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.upsert_device_capability_override(
            device_id,
            capability_id=capability_id,
            calibration_offset=offset,
            calibration_scale=scale,
            notes=notes,
        )
