from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import quote

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


class AlertsApiMixin:
    def list_alert_channels(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertChannelListResponse:
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = self._request("GET", "/api/v1/alerts/channels", params={k: v for k, v in params.items() if v is not None})
        return AlertChannelListResponse.model_validate(data)

    def get_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        data = self._request("GET", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")
        return AlertChannelResponse.model_validate(data)

    def create_alert_channel(self, payload: AlertChannelCreate) -> AlertChannelResponse:
        data = self._request("POST", "/api/v1/alerts/channels", json=payload.model_dump(mode="json", exclude_none=True))
        return AlertChannelResponse.model_validate(data)

    def update_alert_channel(self, channel_id: str, payload: AlertChannelUpdate) -> AlertChannelResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/alerts/channels/{quote(channel_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertChannelResponse.model_validate(data)

    def delete_alert_channel(self, channel_id: str) -> None:
        self._request("DELETE", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")

    def test_alert_channel(self, channel_id: str) -> AlertTestResponse:
        data = self._request("POST", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}/test")
        return AlertTestResponse.model_validate(data)

    def enable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        return self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=True))

    def disable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        return self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=False))

    def list_alert_rules(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertRuleListResponse:
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = self._request("GET", "/api/v1/alerts/rules", params={k: v for k, v in params.items() if v is not None})
        return AlertRuleListResponse.model_validate(data)

    def get_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        data = self._request("GET", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")
        return AlertRuleResponse.model_validate(data)

    def create_alert_rule(self, payload: AlertRuleCreate) -> AlertRuleResponse:
        data = self._request("POST", "/api/v1/alerts/rules", json=payload.model_dump(mode="json", exclude_none=True))
        return AlertRuleResponse.model_validate(data)

    def update_alert_rule(self, rule_id: str, payload: AlertRuleUpdate) -> AlertRuleResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/alerts/rules/{quote(rule_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertRuleResponse.model_validate(data)

    def delete_alert_rule(self, rule_id: str) -> None:
        self._request("DELETE", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")

    def enable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        return self.update_alert_rule(rule_id, AlertRuleUpdate(enabled=True))

    def disable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        return self.update_alert_rule(rule_id, AlertRuleUpdate(enabled=False))

    def list_alert_history(
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
        data = self._request("GET", "/api/v1/alerts/history", params={k: v for k, v in params.items() if v is not None})
        return AlertHistoryListResponse.model_validate(data)

    def iter_alert_channels(self, *, enabled: bool | None = None, page_size: int = 100) -> Iterator[AlertChannelResponse]:
        offset = 0
        while True:
            page = self.list_alert_channels(enabled=enabled, limit=page_size, offset=offset)
            for channel in page.channels:
                yield channel
            offset += len(page.channels)
            if offset >= page.total or not page.channels:
                break

    def iter_alert_rules(self, *, enabled: bool | None = None, page_size: int = 100) -> Iterator[AlertRuleResponse]:
        offset = 0
        while True:
            page = self.list_alert_rules(enabled=enabled, limit=page_size, offset=offset)
            for rule in page.rules:
                yield rule
            offset += len(page.rules)
            if offset >= page.total or not page.rules:
                break

    def iter_alert_history(
        self,
        *,
        device_id: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        page_size: int = 100,
    ) -> Iterator[AlertHistoryResponse]:
        offset = 0
        while True:
            page = self.list_alert_history(
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
