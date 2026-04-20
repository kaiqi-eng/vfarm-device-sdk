from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import (
    CapabilityGroupCreate,
    CapabilityGroupListResponse,
    CapabilityGroupResponse,
    CapabilityGroupUpdate,
)


class AsyncCapabilityGroupsApiMixin:
    async def list_capability_groups(self, *, include_inactive: bool = False) -> CapabilityGroupListResponse:
        """
        List capability groups.

        Parameters
        ----------
        include_inactive:
            Include inactive groups when ``True``.

        Returns
        -------
        CapabilityGroupListResponse
            Capability group list response.

        Examples
        --------
        .. code-block:: python

           page = await client.list_capability_groups(include_inactive=True)
           print(page.total)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", "/api/v1/capability-groups", params={"include_inactive": include_inactive})
        return CapabilityGroupListResponse.model_validate(data)

    async def get_capability_group(self, group_id: str) -> CapabilityGroupResponse:
        """
        Fetch a capability group by ID.

        Parameters
        ----------
        group_id:
            Group identifier.

        Returns
        -------
        CapabilityGroupResponse
            Capability group record.

        Examples
        --------
        .. code-block:: python

           group = await client.get_capability_group("env")
           print(group.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Group not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/capability-groups/{quote(group_id, safe='')}")
        return CapabilityGroupResponse.model_validate(data)

    async def create_capability_group(self, payload: CapabilityGroupCreate) -> CapabilityGroupResponse:
        """
        Create a capability group.

        Parameters
        ----------
        payload:
            Group creation payload.

        Returns
        -------
        CapabilityGroupResponse
            Created group.

        Examples
        --------
        .. code-block:: python

           created = await client.create_capability_group(payload)
           print(created.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid group payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Group already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("POST", "/api/v1/capability-groups", json=payload.model_dump(mode="json", exclude_none=True))
        return CapabilityGroupResponse.model_validate(data)

    async def update_capability_group(self, group_id: str, payload: CapabilityGroupUpdate) -> CapabilityGroupResponse:
        """
        Update a capability group.

        Parameters
        ----------
        group_id:
            Group identifier.
        payload:
            Group update payload.

        Returns
        -------
        CapabilityGroupResponse
            Updated group.

        Examples
        --------
        .. code-block:: python

           updated = await client.update_capability_group("env", payload)
           print(updated.name)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Group not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CapabilityGroupResponse.model_validate(data)

    async def delete_capability_group(self, group_id: str) -> None:
        """
        Delete a capability group.

        Parameters
        ----------
        group_id:
            Group identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.delete_capability_group("env")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Group not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/capability-groups/{quote(group_id, safe='')}")

    async def add_capability_to_group(self, group_id: str, capability_id: str, *, display_order: int = 100) -> None:
        """
        Add a capability to a group.

        Parameters
        ----------
        group_id:
            Group identifier.
        capability_id:
            Capability identifier.
        display_order:
            Ordering index in the group.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.add_capability_to_group("env", "temperature", display_order=10)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Group/capability not found.
        - ``409`` -> ``ConflictError``: Membership already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request(
            "POST",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
            params={"display_order": display_order},
        )

    async def remove_capability_from_group(self, group_id: str, capability_id: str) -> None:
        """
        Remove a capability from a group.

        Parameters
        ----------
        group_id:
            Group identifier.
        capability_id:
            Capability identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.remove_capability_from_group("env", "temperature")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Membership not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request(
            "DELETE",
            f"/api/v1/capability-groups/{quote(group_id, safe='')}/capabilities/{quote(capability_id, safe='')}",
        )

    async def ensure_capability_group(self, payload: CapabilityGroupCreate) -> CapabilityGroupResponse:
        """
        Ensure a capability group exists, creating when missing.

        Parameters
        ----------
        payload:
            Group creation payload.

        Returns
        -------
        CapabilityGroupResponse
            Existing or created group.

        Examples
        --------
        .. code-block:: python

           group = await client.ensure_capability_group(payload)
           print(group.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid group payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Follow-up read failed.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            return await self.create_capability_group(payload)
        except ConflictError:
            return await self.get_capability_group(payload.id)

    async def iter_capability_groups(self, *, include_inactive: bool = False) -> AsyncIterator[CapabilityGroupResponse]:
        """
        Iterate capability groups from list response.

        Parameters
        ----------
        include_inactive:
            Include inactive groups when ``True``.

        Returns
        -------
        AsyncIterator[CapabilityGroupResponse]
            Group iterator.

        Examples
        --------
        .. code-block:: python

           async for group in client.iter_capability_groups():
               print(group.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        page = await self.list_capability_groups(include_inactive=include_inactive)
        for group in page.groups:
            yield group
