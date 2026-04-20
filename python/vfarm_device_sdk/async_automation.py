from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

from .idempotency import with_idempotency_header
from .models import (
    AutomationHistoryResponse,
    AutomationHistoryListResponse,
    AutomationRuleCreate,
    AutomationRuleListResponse,
    AutomationRuleResponse,
    AutomationRuleUpdate,
    AutomationStatsResponse,
)


class AsyncAutomationApiMixin:
    async def list_automation_rules(
        self,
        *,
        enabled: bool | None = None,
        trigger_on: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AutomationRuleListResponse:
        """
        List automation rules with optional filters.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        trigger_on:
            Optional trigger type filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        AutomationRuleListResponse
            Paged automation rules.

        Examples
        --------
        .. code-block:: python

           page = await client.list_automation_rules(enabled=True, limit=20)
           print(page.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "enabled": enabled,
            "trigger_on": trigger_on,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/automation/rules", params={k: v for k, v in params.items() if v is not None})
        return AutomationRuleListResponse.model_validate(data)

    async def get_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        """
        Fetch an automation rule by ID.

        Parameters
        ----------
        rule_id:
            Rule identifier.

        Returns
        -------
        AutomationRuleResponse
            Automation rule record.

        Examples
        --------
        .. code-block:: python

           rule = await client.get_automation_rule("rule-1")
           print(rule.id)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", f"/api/v1/automation/rules/{quote(rule_id, safe='')}")
        return AutomationRuleResponse.model_validate(data)

    async def create_automation_rule(
        self,
        payload: AutomationRuleCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AutomationRuleResponse:
        """
        Create an automation rule.

        Parameters
        ----------
        payload:
            Rule creation payload.
        idempotency_key:
            Optional idempotency key.

        Returns
        -------
        AutomationRuleResponse
            Created rule.

        Examples
        --------
        .. code-block:: python

           rule = await client.create_automation_rule(payload)
           print(rule.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid rule payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``409`` -> ``ConflictError``: Rule conflict.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "POST",
            "/api/v1/automation/rules",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AutomationRuleResponse.model_validate(data)

    async def update_automation_rule(self, rule_id: str, payload: AutomationRuleUpdate) -> AutomationRuleResponse:
        """
        Update an automation rule.

        Parameters
        ----------
        rule_id:
            Rule identifier.
        payload:
            Rule update payload.

        Returns
        -------
        AutomationRuleResponse
            Updated rule.

        Examples
        --------
        .. code-block:: python

           rule = await client.update_automation_rule("rule-1", payload)
           print(rule.enabled)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid update payload.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request(
            "PATCH",
            f"/api/v1/automation/rules/{quote(rule_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AutomationRuleResponse.model_validate(data)

    async def delete_automation_rule(self, rule_id: str) -> None:
        """
        Delete an automation rule.

        Parameters
        ----------
        rule_id:
            Rule identifier.

        Returns
        -------
        None
            Returns ``None`` on success.

        Examples
        --------
        .. code-block:: python

           await client.delete_automation_rule("rule-1")

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        await self._request("DELETE", f"/api/v1/automation/rules/{quote(rule_id, safe='')}")

    async def enable_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        """
        Enable an automation rule.

        Parameters
        ----------
        rule_id:
            Rule identifier.

        Returns
        -------
        AutomationRuleResponse
            Updated enabled rule.

        Examples
        --------
        .. code-block:: python

           rule = await client.enable_automation_rule("rule-1")
           print(rule.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return await self.update_automation_rule(rule_id, AutomationRuleUpdate(enabled=True))

    async def disable_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        """
        Disable an automation rule.

        Parameters
        ----------
        rule_id:
            Rule identifier.

        Returns
        -------
        AutomationRuleResponse
            Updated disabled rule.

        Examples
        --------
        .. code-block:: python

           rule = await client.disable_automation_rule("rule-1")
           print(rule.enabled)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``404`` -> ``NotFoundError``: Rule not found.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        return await self.update_automation_rule(rule_id, AutomationRuleUpdate(enabled=False))

    async def get_automation_stats(self) -> AutomationStatsResponse:
        """
        Fetch automation engine stats.

        Parameters
        ----------
        None
            This method takes no parameters.

        Returns
        -------
        AutomationStatsResponse
            Aggregated automation stats.

        Examples
        --------
        .. code-block:: python

           stats = await client.get_automation_stats()
           print(stats.total_rules)

        Common Errors
        -------------
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        data = await self._request("GET", "/api/v1/automation/stats")
        return AutomationStatsResponse.model_validate(data)

    async def list_automation_history(
        self,
        *,
        rule_id: str | None = None,
        source_device_id: str | None = None,
        status: str | None = None,
        conditions_met: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AutomationHistoryListResponse:
        """
        List automation execution history with filters.

        Parameters
        ----------
        rule_id:
            Optional rule filter.
        source_device_id:
            Optional source device filter.
        status:
            Optional execution status filter.
        conditions_met:
            Optional conditions-met filter.
        limit:
            Page size.
        offset:
            Page offset.

        Returns
        -------
        AutomationHistoryListResponse
            Paged history records.

        Examples
        --------
        .. code-block:: python

           history = await client.list_automation_history(limit=20)
           print(history.total)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        params = {
            "rule_id": rule_id,
            "source_device_id": source_device_id,
            "status": status,
            "conditions_met": conditions_met,
            "limit": limit,
            "offset": offset,
        }
        data = await self._request("GET", "/api/v1/automation/history", params={k: v for k, v in params.items() if v is not None})
        return AutomationHistoryListResponse.model_validate(data)

    async def iter_automation_rules(
        self,
        *,
        enabled: bool | None = None,
        trigger_on: str | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[AutomationRuleResponse]:
        """
        Iterate automation rules using automatic pagination.

        Parameters
        ----------
        enabled:
            Optional enabled-state filter.
        trigger_on:
            Optional trigger filter.
        page_size:
            Page size for each request.

        Returns
        -------
        AsyncIterator[AutomationRuleResponse]
            Rule iterator.

        Examples
        --------
        .. code-block:: python

           async for rule in client.iter_automation_rules(page_size=50):
               print(rule.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = await self.list_automation_rules(enabled=enabled, trigger_on=trigger_on, limit=page_size, offset=offset)
            for rule in page.rules:
                yield rule
            offset += len(page.rules)
            if offset >= page.total or not page.rules:
                break

    async def iter_automation_history(
        self,
        *,
        rule_id: str | None = None,
        source_device_id: str | None = None,
        status: str | None = None,
        conditions_met: bool | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[AutomationHistoryResponse]:
        """
        Iterate automation history using automatic pagination.

        Parameters
        ----------
        rule_id:
            Optional rule filter.
        source_device_id:
            Optional source device filter.
        status:
            Optional execution status filter.
        conditions_met:
            Optional conditions-met filter.
        page_size:
            Page size for each request.

        Returns
        -------
        AsyncIterator[AutomationHistoryResponse]
            History iterator.

        Examples
        --------
        .. code-block:: python

           async for row in client.iter_automation_history(page_size=100):
               print(row.id)

        Common Errors
        -------------
        - ``400/422`` -> ``ValidationError``: Invalid query parameters.
        - ``401`` -> ``AuthenticationError``: Invalid farm API key.
        - ``5xx`` -> ``VFarmApiError``: Server-side failure.
        """
        offset = 0
        while True:
            page = await self.list_automation_history(
                rule_id=rule_id,
                source_device_id=source_device_id,
                status=status,
                conditions_met=conditions_met,
                limit=page_size,
                offset=offset,
            )
            for row in page.history:
                yield row
            offset += len(page.history)
            if offset >= page.total or not page.history:
                break
