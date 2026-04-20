from __future__ import annotations

from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    SensorTypeCreate,
    SensorTypeListResponse,
    SensorTypeResponse,
    SensorTypeUpdate,
)


class AsyncSensorTypeApiMixin:
    async def list_sensor_types(
        self,
        *,
        communication: str | None = None,
        manufacturer: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> SensorTypeListResponse:
        """
        List sensor types with optional filters.

        Parameters
        ----------
        communication:
            Optional communication mode filter.
        manufacturer:
            Optional manufacturer filter.
        is_active:
            Optional active-state filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        SensorTypeListResponse
            Paged sensor type list.

        Examples
        --------
        .. code-block:: python

           page = await client.list_sensor_types(is_active=True, limit=20)
           print(page.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "communication": communication,
            "manufacturer": manufacturer,
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/sensor-types", params={k: v for k, v in params.items() if v is not None})
        return SensorTypeListResponse.model_validate(data)

    async def get_sensor_type(self, sensor_type_id: str) -> SensorTypeResponse:
        """
        Fetch a sensor type by ID.

        Parameters
        ----------
        sensor_type_id:
            Sensor type identifier.

        Returns
        -------
        SensorTypeResponse
            Sensor type record.

        Examples
        --------
        .. code-block:: python

           st = await client.get_sensor_type("dht22")
           print(st.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Sensor type not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}")
        return SensorTypeResponse.model_validate(data)

    async def create_sensor_type(self, payload: SensorTypeCreate) -> SensorTypeResponse:
        """
        Create a sensor type.

        Parameters
        ----------
        payload:
            Sensor type creation payload.

        Returns
        -------
        SensorTypeResponse
            Created sensor type record.

        Examples
        --------
        .. code-block:: python

           created = await client.create_sensor_type(payload)
           print(created.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid sensor type payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Sensor type already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("POST", "/api/v1/sensor-types", json=payload.model_dump(mode="json", exclude_none=True))
        return SensorTypeResponse.model_validate(data)

    async def update_sensor_type(self, sensor_type_id: str, payload: SensorTypeUpdate) -> SensorTypeResponse:
        """
        Update a sensor type.

        Parameters
        ----------
        sensor_type_id:
            Sensor type identifier.
        payload:
            Sensor type update payload.

        Returns
        -------
        SensorTypeResponse
            Updated sensor type record.

        Examples
        --------
        .. code-block:: python

           updated = await client.update_sensor_type("dht22", payload)
           print(updated.name)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Sensor type not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return SensorTypeResponse.model_validate(data)

    async def delete_sensor_type(self, sensor_type_id: str) -> None:
        """
        Delete a sensor type by ID.

        Parameters
        ----------
        sensor_type_id:
            Sensor type identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.delete_sensor_type("dht22")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Sensor type not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}")

    async def remove_sensor_type_capability(self, sensor_type_id: str, capability_id: str) -> None:
        """
        Remove capability linkage from a sensor type.

        Parameters
        ----------
        sensor_type_id:
            Sensor type identifier.
        capability_id:
            Capability identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.remove_sensor_type_capability("dht22", "temperature")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Linkage not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request(
            "DELETE",
            f"/api/v1/sensor-types/{quote(sensor_type_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    async def ensure_sensor_type(self, payload: SensorTypeCreate) -> SensorTypeResponse:
        """
        Ensure a sensor type exists, creating when missing.

        Parameters
        ----------
        payload:
            Sensor type creation payload.

        Returns
        -------
        SensorTypeResponse
            Existing or created sensor type.

        Examples
        --------
        .. code-block:: python

           st = await client.ensure_sensor_type(payload)
           print(st.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid sensor type payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Follow-up read failed.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            return await self.create_sensor_type(payload)
        except ConflictError:
            return await self.get_sensor_type(payload.id)
