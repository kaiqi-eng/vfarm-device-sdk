from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    CapabilityCreate,
    CapabilityListResponse,
    CapabilityResponse,
    CapabilityUpdate,
)


class AsyncCapabilitiesApiMixin:
    async def list_capabilities(
        self,
        *,
        category: str | None = None,
        data_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CapabilityListResponse:
        """
        List capabilities with optional filters.

        Parameters
        ----------
        category:
            Optional category filter.
        data_type:
            Optional data-type filter.
        is_active:
            Optional active-state filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        CapabilityListResponse
            Paged capability list.

        Examples
        --------
        .. code-block:: python

           page = await client.list_capabilities(limit=50)
           print(page.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "category": category,
            "data_type": data_type,
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/capabilities", params={k: v for k, v in params.items() if v is not None})
        return CapabilityListResponse.model_validate(data)

    async def get_capability(self, capability_id: str) -> CapabilityResponse:
        """
        Fetch a capability by ID.

        Parameters
        ----------
        capability_id:
            Capability identifier.

        Returns
        -------
        CapabilityResponse
            Capability record.

        Examples
        --------
        .. code-block:: python

           cap = await client.get_capability("temperature")
           print(cap.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Capability not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/capabilities/{quote(capability_id, safe='')}")
        return CapabilityResponse.model_validate(data)

    async def create_capability(self, payload: CapabilityCreate) -> CapabilityResponse:
        """
        Create a capability.

        Parameters
        ----------
        payload:
            Capability creation payload.

        Returns
        -------
        CapabilityResponse
            Created capability.

        Examples
        --------
        .. code-block:: python

           created = await client.create_capability(payload)
           print(created.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid capability payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Capability already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("POST", "/api/v1/capabilities", json=payload.model_dump(mode="json", exclude_none=True))
        return CapabilityResponse.model_validate(data)

    async def update_capability(self, capability_id: str, payload: CapabilityUpdate) -> CapabilityResponse:
        """
        Update a capability.

        Parameters
        ----------
        capability_id:
            Capability identifier.
        payload:
            Capability update payload.

        Returns
        -------
        CapabilityResponse
            Updated capability.

        Examples
        --------
        .. code-block:: python

           updated = await client.update_capability("temperature", payload)
           print(updated.name)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Capability not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/capabilities/{quote(capability_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CapabilityResponse.model_validate(data)

    async def delete_capability(self, capability_id: str) -> None:
        """
        Delete a capability by ID.

        Parameters
        ----------
        capability_id:
            Capability identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.delete_capability("temperature")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Capability not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/capabilities/{quote(capability_id, safe='')}")

    async def ensure_capability(self, payload: CapabilityCreate) -> CapabilityResponse:
        """
        Ensure a capability exists, creating when missing.

        Parameters
        ----------
        payload:
            Capability creation payload.

        Returns
        -------
        CapabilityResponse
            Existing or created capability.

        Examples
        --------
        .. code-block:: python

           cap = await client.ensure_capability(payload)
           print(cap.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid capability payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Follow-up read failed.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            return await self.create_capability(payload)
        except ConflictError:
            return await self.get_capability(payload.id)

    async def iter_capabilities(
        self,
        *,
        category: str | None = None,
        data_type: str | None = None,
        is_active: bool | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[CapabilityResponse]:
        """
        Iterate capabilities using automatic pagination.

        Parameters
        ----------
        category:
            Optional category filter.
        data_type:
            Optional data-type filter.
        is_active:
            Optional active-state filter.
        page_size:
            Page size for each API request.

        Returns
        -------
        AsyncIterator[CapabilityResponse]
            Capability iterator.

        Examples
        --------
        .. code-block:: python

           async for cap in client.iter_capabilities(page_size=100):
               print(cap.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = await self.list_capabilities(
                category=category,
                data_type=data_type,
                is_active=is_active,
                limit=page_size,
                offset=offset,
            )
            for capability in page.capabilities:
                yield capability
            offset += len(page.capabilities)
            if offset >= page.total or not page.capabilities:
                break
