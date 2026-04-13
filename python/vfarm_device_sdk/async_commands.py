from __future__ import annotations

from typing import Literal

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
        merged = dict(payload)
        if payload_extra:
            # Intentionally allow extra keys to override typed payload keys.
            merged.update(payload_extra)
        return merged

    async def fetch_pending_commands(self, device_id: str, *, limit: int = 10) -> PendingCommandsResponse:
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
        params: dict[str, object] = {
            "limit": limit,
            "offset": offset,
        }
        if status is not None:
            params["status"] = status
        data = await self._request("GET", f"/api/v1/devices/{device_id}/commands", params=params)
        return CommandListResponse.model_validate(data)

    async def create_command(self, device_id: str, payload: CommandCreate) -> CommandResponse:
        data = await self._request(
            "POST",
            f"/api/v1/devices/{device_id}/commands",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CommandResponse.model_validate(data)

    async def update_command_status(
        self,
        device_id: str,
        command_id: str,
        payload: CommandAcknowledge,
    ) -> CommandResponse:
        data = await self._request(
            "PATCH",
            f"/api/v1/devices/{device_id}/commands/{command_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CommandResponse.model_validate(data)

    async def cancel_command(self, device_id: str, command_id: str) -> None:
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
    ) -> CommandResponse:
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
    ) -> CommandResponse:
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
    ) -> CommandResponse:
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
    ) -> CommandResponse:
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
    ) -> CommandResponse:
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
        )
