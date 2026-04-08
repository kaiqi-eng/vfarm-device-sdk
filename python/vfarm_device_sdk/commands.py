from __future__ import annotations

from .models import (
    CommandAcknowledge,
    CommandCreate,
    CommandListResponse,
    CommandResponse,
    PendingCommandsResponse,
)


class CommandApiMixin:
    def fetch_pending_commands(self, device_id: str, *, limit: int = 10) -> PendingCommandsResponse:
        data = self._request(
            "GET",
            f"/api/v1/devices/{device_id}/commands/pending",
            params={"limit": limit},
        )
        return PendingCommandsResponse.model_validate(data)

    def list_device_commands(
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
        data = self._request("GET", f"/api/v1/devices/{device_id}/commands", params=params)
        return CommandListResponse.model_validate(data)

    def create_command(self, device_id: str, payload: CommandCreate) -> CommandResponse:
        data = self._request(
            "POST",
            f"/api/v1/devices/{device_id}/commands",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CommandResponse.model_validate(data)

    def update_command_status(
        self,
        device_id: str,
        command_id: str,
        payload: CommandAcknowledge,
    ) -> CommandResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/devices/{device_id}/commands/{command_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return CommandResponse.model_validate(data)

    def cancel_command(self, device_id: str, command_id: str) -> None:
        self._request("DELETE", f"/api/v1/devices/{device_id}/commands/{command_id}")

    def enqueue_config_update(
        self,
        device_id: str,
        *,
        changes: dict[str, object],
        merge_strategy: str = "patch",
        priority: int = 100,
        ttl_minutes: int = 60,
        notes: str | None = None,
    ) -> CommandResponse:
        return self.create_command(
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

    def enqueue_restart_service(
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
        return self.create_command(
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
