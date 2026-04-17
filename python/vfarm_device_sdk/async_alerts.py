from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .idempotency import with_idempotency_header
from .models import (
    AlertChannelCreate,
    AlertChannelListResponse,
    AlertChannelResponse,
    AlertChannelUpdate,
    AlertHistoryListResponse,
    AlertHistoryResponse,
    AlertRuleCreate,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertTestResponse,
)


class AsyncAlertsApiMixin:
    async def list_alert_channels(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertChannelListResponse:
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = await self._request("GET", "/api/v1/alerts/channels", params={k: v for k, v in params.items() if v is not None})
        return AlertChannelListResponse.model_validate(data)

    async def get_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        data = await self._request("GET", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")
        return AlertChannelResponse.model_validate(data)

    async def create_alert_channel(
        self,
        payload: AlertChannelCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AlertChannelResponse:
        data = await self._request(
            "POST",
            "/api/v1/alerts/channels",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AlertChannelResponse.model_validate(data)

    async def update_alert_channel(self, channel_id: str, payload: AlertChannelUpdate) -> AlertChannelResponse:
        data = await self._request(
            "PATCH",
            f"/api/v1/alerts/channels/{quote(channel_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertChannelResponse.model_validate(data)

    async def delete_alert_channel(self, channel_id: str) -> None:
        await self._request("DELETE", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")

    async def test_alert_channel(self, channel_id: str) -> AlertTestResponse:
        data = await self._request("POST", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}/test")
        return AlertTestResponse.model_validate(data)

    async def enable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        return await self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=True))

    async def disable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        return await self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=False))

    async def list_alert_rules(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertRuleListResponse:
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = await self._request("GET", "/api/v1/alerts/rules", params={k: v for k, v in params.items() if v is not None})
        return AlertRuleListResponse.model_validate(data)

    async def get_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        data = await self._request("GET", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")
        return AlertRuleResponse.model_validate(data)

    async def create_alert_rule(
        self,
        payload: AlertRuleCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AlertRuleResponse:
        data = await self._request(
            "POST",
            "/api/v1/alerts/rules",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AlertRuleResponse.model_validate(data)

    async def update_alert_rule(self, rule_id: str, payload: AlertRuleUpdate) -> AlertRuleResponse:
        data = await self._request(
            "PATCH",
            f"/api/v1/alerts/rules/{quote(rule_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertRuleResponse.model_validate(data)

    async def delete_alert_rule(self, rule_id: str) -> None:
        await self._request("DELETE", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")

    async def enable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        return await self.update_alert_rule(rule_id, AlertRuleUpdate(enabled=True))

    async def disable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        return await self.update_alert_rule(rule_id, AlertRuleUpdate(enabled=False))

    async def list_alert_history(
        self,
        *,
        device_id: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertHistoryListResponse:
        params = {
            "device_id": device_id,
            "event_type": event_type,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/alerts/history", params={k: v for k, v in params.items() if v is not None})
        return AlertHistoryListResponse.model_validate(data)

    async def iter_alert_channels(self, *, enabled: bool | None = None, page_size: int = 100) -> AsyncIterator[AlertChannelResponse]:
        offset = 0
        while True:
            page = await self.list_alert_channels(enabled=enabled, limit=page_size, offset=offset)
            for channel in page.channels:
                yield channel
            offset += len(page.channels)
            if offset >= page.total or not page.channels:
                break

    async def iter_alert_rules(self, *, enabled: bool | None = None, page_size: int = 100) -> AsyncIterator[AlertRuleResponse]:
        offset = 0
        while True:
            page = await self.list_alert_rules(enabled=enabled, limit=page_size, offset=offset)
            for rule in page.rules:
                yield rule
            offset += len(page.rules)
            if offset >= page.total or not page.rules:
                break

    async def iter_alert_history(
        self,
        *,
        device_id: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[AlertHistoryResponse]:
        offset = 0
        while True:
            page = await self.list_alert_history(
                device_id=device_id,
                event_type=event_type,
                status=status,
                limit=page_size,
                offset=offset,
            )
            for row in page.alerts:
                yield row
            offset += len(page.alerts)
            if offset >= page.total or not page.alerts:
                break
