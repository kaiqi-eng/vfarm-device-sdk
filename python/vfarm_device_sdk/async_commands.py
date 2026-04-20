from __future__ import annotations

from typing import Literal

from .idempotency import with_idempotency_header
from .models import (
    CommandAcknowledge,
    CommandCreate,
    CommandListResponse,
    CommandResponse,
    CustomPayload,
    PendingCommandsResponse,
    SetStatePayload,
    SetValuePayload,
)


class AsyncCommandApiMixin:
    @staticmethod
    def _merge_payload_extra(
        payload: dict[str, object],
        payload_extra: dict[str, object] | None,
    ) -> dict[str, object]:
        """
        Merge typed payload with optional override payload.

        Parameters
        ----------
        payload:
            Base typed payload dict.
        payload_extra:
            Optional extra keys; overrides existing keys when duplicated.

        Returns
        -------
        dict[str, object]
            Merged payload dictionary.

        Examples
        --------
        .. code-block:: python

           merged = AsyncCommandApiMixin._merge_payload_extra({"target": "relay"}, {"target": "fan"})
           print(merged["target"])

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Pure helper; no API request.
        """
        merged = dict(payload)
        if payload_extra:
            # Intentionally allow extra keys to override typed payload keys.
            merged.update(payload_extra)
        return merged

    async def fetch_pending_commands(self, device_id: str, *, limit: int = 10) -> PendingCommandsResponse:
        """
        Fetch pending commands for a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        limit:
            Maximum commands to return.

        Returns
        -------
        PendingCommandsResponse
            Pending command list.

        Examples
        --------
        .. code-block:: python

           pending = await client.fetch_pending_commands("sensor-001", limit=5)
           print(len(pending.commands))

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "GET",
            f"/api/v1/devices/{device_id}/commands/pending",
            params={"limit": limit},
        )
        return PendingCommandsResponse.model_validate(data)

    async def list_device_commands(
        self,
        device_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CommandListResponse:
        """
        List commands for a device with optional status filtering.

        Parameters
        ----------
        device_id:
            Device identifier.
        status:
            Optional command status filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        CommandListResponse
            Command history page.

        Examples
        --------
        .. code-block:: python

           page = await client.list_device_commands("sensor-001", status="pending")
           print(page.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid filter values.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params: dict[str, object] = {
            "limit": limit,
            "offset": offset,
        }
        if status is not None:
            params["status"] = status
        data = await self._request("GET", f"/api/v1/devices/{device_id}/commands", params=params)
        return CommandListResponse.model_validate(data)

    async def create_command(
        self,
        device_id: str,
        payload: CommandCreate,
        *,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Create a command for a device.

        Parameters
        ----------
        device_id:
            Device identifier.
        payload:
            Command creation payload.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.create_command("sensor-001", CommandCreate(command_type="custom", payload={"action": "sync"}))
           print(cmd.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``409`` -> ``ConflictError``: Conflicting command state.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "POST",
            f"/api/v1/devices/{device_id}/commands",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return CommandResponse.model_validate(data)

    async def update_command_status(
        self,
        device_id: str,
        command_id: str,
        payload: CommandAcknowledge,
    ) -> CommandResponse:
        """
        Update a command status (for example acknowledged/completed).

        Parameters
        ----------
        device_id:
            Device identifier.
        command_id:
            Command identifier.
        payload:
            Status update payload.

        Returns
        -------
        CommandResponse
            Updated command response.

        Examples
        --------
        .. code-block:: python

           updated = await client.update_command_status("sensor-001", "cmd-1", CommandAcknowledge(status="acknowledged"))
           print(updated.status)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid status payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/command not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/devices/{device_id}/commands/{command_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CommandResponse.model_validate(data)

    async def cancel_command(self, device_id: str, command_id: str) -> None:
        """
        Cancel a command by ID.

        Parameters
        ----------
        device_id:
            Device identifier.
        command_id:
            Command identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.cancel_command("sensor-001", "cmd-1")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device/command not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/devices/{device_id}/commands/{command_id}")

    async def enqueue_config_update(
        self,
        device_id: str,
        *,
        changes: dict[str, object],
        merge_strategy: str = "patch",
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Enqueue a typed ``config_update`` command.

        Parameters
        ----------
        device_id:
            Device identifier.
        changes:
            Configuration changes map.
        merge_strategy:
            Merge behavior (for example ``patch``).
        priority:
            Command priority.
        ttl_minutes:
            Expiry TTL in minutes.
        notes:
            Optional notes.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.enqueue_config_update("sensor-001", changes={"poll_interval_s": 30})
           print(cmd.command_type)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return await self.create_command(
            device_id,
            CommandCreate(
                command_type="config_update",
                payload={
                    "changes": changes,
                    "merge_strategy": merge_strategy,
                },
                priority=priority,
                ttl_minutes=ttl_minutes,
                notes=notes,
            ),
            idempotency_key=idempotency_key,
        )

    async def enqueue_restart_service(
        self,
        device_id: str,
        *,
        reason: str | None = None,
        delay_seconds: int = 5,
        graceful: bool = True,
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Enqueue a typed ``restart_service`` command.

        Parameters
        ----------
        device_id:
            Device identifier.
        reason:
            Optional restart reason.
        delay_seconds:
            Delay before restart.
        graceful:
            Whether restart should be graceful.
        priority:
            Command priority.
        ttl_minutes:
            Expiry TTL in minutes.
        notes:
            Optional notes.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.enqueue_restart_service("sensor-001", reason="firmware apply")
           print(cmd.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return await self.create_command(
            device_id,
            CommandCreate(
                command_type="restart_service",
                payload={
                    "reason": reason,
                    "delay_seconds": delay_seconds,
                    "graceful": graceful,
                },
                priority=priority,
                ttl_minutes=ttl_minutes,
                notes=notes,
            ),
            idempotency_key=idempotency_key,
        )

    async def enqueue_set_state(
        self,
        device_id: str,
        *,
        target: str,
        state: Literal["on", "off"],
        reason: str | None = None,
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
        payload_extra: dict[str, object] | None = None,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Enqueue a typed ``set_state`` command.

        Parameters
        ----------
        device_id:
            Device identifier.
        target:
            Target actuator/component.
        state:
            Desired state (``on`` or ``off``).
        reason:
            Optional reason.
        priority:
            Command priority.
        ttl_minutes:
            Expiry TTL in minutes.
        notes:
            Optional notes.
        payload_extra:
            Optional payload overrides.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.enqueue_set_state("sensor-001", target="relay-1", state="on")
           print(cmd.command_type)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        typed_payload = SetStatePayload(
            target=target,
            state=state,
            reason=reason,
        ).model_dump(mode="json", exclude_none=True)
        payload = self._merge_payload_extra(typed_payload, payload_extra)
        return await self.create_command(
            device_id,
            CommandCreate(
                command_type="set_state",
                payload=payload,
                priority=priority,
                ttl_minutes=ttl_minutes,
                notes=notes,
            ),
            idempotency_key=idempotency_key,
        )

    async def enqueue_set_value(
        self,
        device_id: str,
        *,
        target: str,
        value: float,
        unit: str | None = None,
        reason: str | None = None,
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
        payload_extra: dict[str, object] | None = None,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Enqueue a typed ``set_value`` command.

        Parameters
        ----------
        device_id:
            Device identifier.
        target:
            Target actuator/component.
        value:
            Desired numeric value.
        unit:
            Optional value unit.
        reason:
            Optional reason.
        priority:
            Command priority.
        ttl_minutes:
            Expiry TTL in minutes.
        notes:
            Optional notes.
        payload_extra:
            Optional payload overrides.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.enqueue_set_value("sensor-001", target="fan-speed", value=42.0, unit="percent")
           print(cmd.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        typed_payload = SetValuePayload(
            target=target,
            value=value,
            unit=unit,
            reason=reason,
        ).model_dump(mode="json", exclude_none=True)
        payload = self._merge_payload_extra(typed_payload, payload_extra)
        return await self.create_command(
            device_id,
            CommandCreate(
                command_type="set_value",
                payload=payload,
                priority=priority,
                ttl_minutes=ttl_minutes,
                notes=notes,
            ),
            idempotency_key=idempotency_key,
        )

    async def enqueue_custom(
        self,
        device_id: str,
        *,
        action: str,
        params: dict[str, object] | None = None,
        reason: str | None = None,
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
        payload_extra: dict[str, object] | None = None,
        idempotency_key: str | None = None,
    ) -> CommandResponse:
        """
        Enqueue a typed ``custom`` command.

        Parameters
        ----------
        device_id:
            Device identifier.
        action:
            Custom action name.
        params:
            Optional action parameters.
        reason:
            Optional reason.
        priority:
            Command priority.
        ttl_minutes:
            Expiry TTL in minutes.
        notes:
            Optional notes.
        payload_extra:
            Optional payload overrides.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        CommandResponse
            Created command response.

        Examples
        --------
        .. code-block:: python

           cmd = await client.enqueue_custom("sensor-001", action="sync_profile", params={"profile": "eco"})
           print(cmd.command_type)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid command payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Device not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        typed_payload = CustomPayload(
            action=action,
            params=params or {},
            reason=reason,
        ).model_dump(mode="json", exclude_none=True)
        payload = self._merge_payload_extra(typed_payload, payload_extra)
        return await self.create_command(
            device_id,
            CommandCreate(
                command_type="custom",
                payload=payload,
                priority=priority,
                ttl_minutes=ttl_minutes,
                notes=notes,
            ),
            idempotency_key=idempotency_key,
        )
