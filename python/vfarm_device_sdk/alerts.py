from __future__ import annotations

from collections.abc import Iterator
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


class AlertsApiMixin:
    def list_alert_channels(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertChannelListResponse:
        """
        List alert channels.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        AlertChannelListResponse
            Paged alert channels.

        Examples
        --------
        .. code-block:: python

           channels = client.list_alert_channels(enabled=True, limit=20)
           print(channels.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = self._request("GET", "/api/v1/alerts/channels", params={k: v for k, v in params.items() if v is not None})
        return AlertChannelListResponse.model_validate(data)

    def get_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        """
        Fetch an alert channel by ID.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.

        Returns
        -------
        AlertChannelResponse
            Alert channel record.

        Examples
        --------
        .. code-block:: python

           channel = client.get_alert_channel("channel-1")
           print(channel.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")
        return AlertChannelResponse.model_validate(data)

    def create_alert_channel(
        self,
        payload: AlertChannelCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AlertChannelResponse:
        """
        Create an alert channel.

        Parameters
        ----------
        payload:
            Alert channel payload.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        AlertChannelResponse
            Created channel.

        Examples
        --------
        .. code-block:: python

           channel = client.create_alert_channel(payload)
           print(channel.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Channel conflict.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "POST",
            "/api/v1/alerts/channels",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AlertChannelResponse.model_validate(data)

    def update_alert_channel(self, channel_id: str, payload: AlertChannelUpdate) -> AlertChannelResponse:
        """
        Update an alert channel.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.
        payload:
            Alert channel update payload.

        Returns
        -------
        AlertChannelResponse
            Updated channel.

        Examples
        --------
        .. code-block:: python

           updated = client.update_alert_channel("channel-1", payload)
           print(updated.enabled)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "PATCH",
            f"/api/v1/alerts/channels/{quote(channel_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertChannelResponse.model_validate(data)

    def delete_alert_channel(self, channel_id: str) -> None:
        """
        Delete an alert channel.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           client.delete_alert_channel("channel-1")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        self._request("DELETE", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}")

    def test_alert_channel(self, channel_id: str) -> AlertTestResponse:
        """
        Trigger a test notification for an alert channel.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.

        Returns
        -------
        AlertTestResponse
            Test invocation result.

        Examples
        --------
        .. code-block:: python

           result = client.test_alert_channel("channel-1")
           print(result.status)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("POST", f"/api/v1/alerts/channels/{quote(channel_id, safe='')}/test")
        return AlertTestResponse.model_validate(data)

    def enable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        """
        Enable an alert channel.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.

        Returns
        -------
        AlertChannelResponse
            Updated enabled channel.

        Examples
        --------
        .. code-block:: python

           channel = client.enable_alert_channel("channel-1")
           print(channel.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=True))

    def disable_alert_channel(self, channel_id: str) -> AlertChannelResponse:
        """
        Disable an alert channel.

        Parameters
        ----------
        channel_id:
            Alert channel identifier.

        Returns
        -------
        AlertChannelResponse
            Updated disabled channel.

        Examples
        --------
        .. code-block:: python

           channel = client.disable_alert_channel("channel-1")
           print(channel.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Channel not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.update_alert_channel(channel_id, AlertChannelUpdate(enabled=False))

    def list_alert_rules(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertRuleListResponse:
        """
        List alert rules.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        AlertRuleListResponse
            Paged alert rules.

        Examples
        --------
        .. code-block:: python

           rules = client.list_alert_rules(limit=20)
           print(rules.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {"enabled": enabled, "limit": limit, "offset": offset}
        data = self._request("GET", "/api/v1/alerts/rules", params={k: v for k, v in params.items() if v is not None})
        return AlertRuleListResponse.model_validate(data)

    def get_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        """
        Fetch an alert rule by ID.

        Parameters
        ----------
        rule_id:
            Alert rule identifier.

        Returns
        -------
        AlertRuleResponse
            Alert rule record.

        Examples
        --------
        .. code-block:: python

           rule = client.get_alert_rule("rule-1")
           print(rule.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request("GET", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")
        return AlertRuleResponse.model_validate(data)

    def create_alert_rule(
        self,
        payload: AlertRuleCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AlertRuleResponse:
        """
        Create an alert rule.

        Parameters
        ----------
        payload:
            Alert rule payload.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        AlertRuleResponse
            Created alert rule.

        Examples
        --------
        .. code-block:: python

           rule = client.create_alert_rule(payload)
           print(rule.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Rule conflict.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "POST",
            "/api/v1/alerts/rules",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AlertRuleResponse.model_validate(data)

    def update_alert_rule(self, rule_id: str, payload: AlertRuleUpdate) -> AlertRuleResponse:
        """
        Update an alert rule.

        Parameters
        ----------
        rule_id:
            Alert rule identifier.
        payload:
            Alert rule update payload.

        Returns
        -------
        AlertRuleResponse
            Updated alert rule.

        Examples
        --------
        .. code-block:: python

           updated = client.update_alert_rule("rule-1", payload)
           print(updated.enabled)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = self._request(
            "PATCH",
            f"/api/v1/alerts/rules/{quote(rule_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AlertRuleResponse.model_validate(data)

    def delete_alert_rule(self, rule_id: str) -> None:
        """
        Delete an alert rule.

        Parameters
        ----------
        rule_id:
            Alert rule identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           client.delete_alert_rule("rule-1")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        self._request("DELETE", f"/api/v1/alerts/rules/{quote(rule_id, safe='')}")

    def enable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        """
        Enable an alert rule.

        Parameters
        ----------
        rule_id:
            Alert rule identifier.

        Returns
        -------
        AlertRuleResponse
            Updated enabled rule.

        Examples
        --------
        .. code-block:: python

           rule = client.enable_alert_rule("rule-1")
           print(rule.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return self.update_alert_rule(rule_id, AlertRuleUpdate(enabled=True))

    def disable_alert_rule(self, rule_id: str) -> AlertRuleResponse:
        """
        Disable an alert rule.

        Parameters
        ----------
        rule_id:
            Alert rule identifier.

        Returns
        -------
        AlertRuleResponse
            Updated disabled rule.

        Examples
        --------
        .. code-block:: python

           rule = client.disable_alert_rule("rule-1")
           print(rule.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
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
        """
        List alert delivery/history records.

        Parameters
        ----------
        device_id:
            Optional device filter.
        event_type:
            Optional event-type filter.
        status:
            Optional delivery-status filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        AlertHistoryListResponse
            Paged alert history.

        Examples
        --------
        .. code-block:: python

           history = client.list_alert_history(limit=20)
           print(history.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
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
        """
        Iterate alert channels using automatic pagination.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        page_size:
            Page size for each request.

        Returns
        -------
        Iterator[AlertChannelResponse]
            Alert channel iterator.

        Examples
        --------
        .. code-block:: python

           for channel in client.iter_alert_channels(page_size=50):
               print(channel.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = self.list_alert_channels(enabled=enabled, limit=page_size, offset=offset)
            for channel in page.channels:
                yield channel
            offset += len(page.channels)
            if offset >= page.total or not page.channels:
                break

    def iter_alert_rules(self, *, enabled: bool | None = None, page_size: int = 100) -> Iterator[AlertRuleResponse]:
        """
        Iterate alert rules using automatic pagination.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        page_size:
            Page size for each request.

        Returns
        -------
        Iterator[AlertRuleResponse]
            Alert rule iterator.

        Examples
        --------
        .. code-block:: python

           for rule in client.iter_alert_rules(page_size=50):
               print(rule.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
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
        """
        Iterate alert history using automatic pagination.

        Parameters
        ----------
        device_id:
            Optional device filter.
        event_type:
            Optional event-type filter.
        status:
            Optional delivery-status filter.
        page_size:
            Page size for each request.

        Returns
        -------
        Iterator[AlertHistoryResponse]
            Alert history iterator.

        Examples
        --------
        .. code-block:: python

           for row in client.iter_alert_history(page_size=100):
               print(row.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
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
