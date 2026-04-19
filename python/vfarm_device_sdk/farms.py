from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import quote

from .exceptions import ConflictError
from .models import FarmCreate, FarmListResponse, FarmResponse, FarmUpdate


class FarmApiMixin:
    def list_farms(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FarmListResponse:
        """
        List farms with optional active-state filtering.

        Parameters
        ----------
        is_active:
            Optional active flag filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        FarmListResponse
            Paged farm list.

        Examples
        --------
        .. code-block:: python

           page = client.list_farms(is_active=True, limit=20)
           print(page.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "is_active": is_active,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/farms", params={k: v for k, v in params.items() if v is not None})
        return FarmListResponse.model_validate(data)

    def get_farm(self, farm_id: str) -> FarmResponse:
        """
        Fetch a farm by ID.

        Parameters
        ----------
        farm_id:
            Farm identifier.

        Returns
        -------
        FarmResponse
            Farm record.

        Examples
        --------
        .. code-block:: python

           farm = client.get_farm("farm-a")
           print(farm.name)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Farm not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/farms/{quote(farm_id, safe='')}")
        return FarmResponse.model_validate(data)

    def create_farm(
        self,
        *,
        farm_id: str,
        name: str,
        description: str | None = None,
        address: str | None = None,
    ) -> FarmResponse:
        """
        Create a farm.

        Parameters
        ----------
        farm_id:
            Farm identifier.
        name:
            Farm display name.
        description:
            Optional description.
        address:
            Optional address.

        Returns
        -------
        FarmResponse
            Created farm record.

        Examples
        --------
        .. code-block:: python

           farm = client.create_farm(farm_id="farm-a", name="Farm A")
           print(farm.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid farm payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Farm ID already exists.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        payload = FarmCreate(
            id=farm_id,
            name=name,
            description=description,
            address=address,
        )
        data = self._request("POST", "/api/v1/farms", json=payload.model_dump(mode="json", exclude_none=True))
        return FarmResponse.model_validate(data)

    def update_farm(
        self,
        farm_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        address: str | None = None,
        is_active: bool | None = None,
    ) -> FarmResponse:
        """
        Update mutable fields on a farm.

        Parameters
        ----------
        farm_id:
            Farm identifier.
        name:
            Optional updated name.
        description:
            Optional updated description.
        address:
            Optional updated address.
        is_active:
            Optional active-state update.

        Returns
        -------
        FarmResponse
            Updated farm record.

        Examples
        --------
        .. code-block:: python

           farm = client.update_farm("farm-a", address="123 Field Rd")
           print(farm.address)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Farm not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        payload = FarmUpdate(
            name=name,
            description=description,
            address=address,
            is_active=is_active,
        )
        data = self._request(
            "PATCH",
            f"/api/v1/farms/{quote(farm_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return FarmResponse.model_validate(data)

    def delete_farm(self, farm_id: str) -> None:
        """
        Delete a farm by ID.

        Parameters
        ----------
        farm_id:
            Farm identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           client.delete_farm("farm-a")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Farm not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        self._request("DELETE", f"/api/v1/farms/{quote(farm_id, safe='')}")

    def reactivate_farm(self, farm_id: str) -> FarmResponse:
        """
        Mark a farm as active.

        Parameters
        ----------
        farm_id:
            Farm identifier.

        Returns
        -------
        FarmResponse
            Updated farm record.

        Examples
        --------
        .. code-block:: python

           farm = client.reactivate_farm("farm-a")
           print(farm.is_active)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Farm not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.update_farm(farm_id, is_active=True)

    def deactivate_farm(self, farm_id: str) -> FarmResponse:
        """
        Mark a farm as inactive.

        Parameters
        ----------
        farm_id:
            Farm identifier.

        Returns
        -------
        FarmResponse
            Updated farm record.

        Examples
        --------
        .. code-block:: python

           farm = client.deactivate_farm("farm-a")
           print(farm.is_active)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Farm not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.update_farm(farm_id, is_active=False)

    def ensure_farm(
        self,
        *,
        farm_id: str,
        name: str,
        description: str | None = None,
        address: str | None = None,
    ) -> FarmResponse:
        """
        Ensure a farm exists, creating it if missing.

        Parameters
        ----------
        farm_id:
            Farm identifier.
        name:
            Farm display name.
        description:
            Optional description.
        address:
            Optional address.

        Returns
        -------
        FarmResponse
            Existing or newly created farm.

        Examples
        --------
        .. code-block:: python

           farm = client.ensure_farm(farm_id="farm-a", name="Farm A")
           print(farm.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid farm payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Follow-up read could not find farm.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        try:
            return self.create_farm(farm_id=farm_id, name=name, description=description, address=address)
        except ConflictError:
            return self.get_farm(farm_id)

    def iter_farms(
        self,
        *,
        is_active: bool | None = None,
        page_size: int = 100,
    ) -> Iterator[FarmResponse]:
        """
        Iterate farms using automatic pagination.

        Parameters
        ----------
        is_active:
            Optional active flag filter.
        page_size:
            Page size for each request.

        Returns
        -------
        Iterator[FarmResponse]
            Farm iterator.

        Examples
        --------
        .. code-block:: python

           for farm in client.iter_farms(page_size=50):
               print(farm.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = self.list_farms(is_active=is_active, limit=page_size, offset=offset)
            for farm in page.farms:
                yield farm
            offset += len(page.farms)
            if offset >= page.total or not page.farms:
                break
