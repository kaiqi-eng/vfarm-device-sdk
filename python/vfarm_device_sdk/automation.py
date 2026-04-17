from __future__ import annotations

from collections.abc import Iterator
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


class AutomationApiMixin:
    def list_automation_rules(
        self,
        *,
        enabled: bool | None = None,
        trigger_on: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AutomationRuleListResponse:
        params = {
            "enabled": enabled,
            "trigger_on": trigger_on,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/automation/rules", params={k: v for k, v in params.items() if v is not None})
        return AutomationRuleListResponse.model_validate(data)

    def get_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        data = self._request("GET", f"/api/v1/automation/rules/{quote(rule_id, safe='')}")
        return AutomationRuleResponse.model_validate(data)

    def create_automation_rule(
        self,
        payload: AutomationRuleCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AutomationRuleResponse:
        data = self._request(
            "POST",
            "/api/v1/automation/rules",
            json=payload.model_dump(mode="json", exclude_none=True),
            headers=with_idempotency_header(headers=None, idempotency_key=idempotency_key),
        )
        return AutomationRuleResponse.model_validate(data)

    def update_automation_rule(self, rule_id: str, payload: AutomationRuleUpdate) -> AutomationRuleResponse:
        data = self._request(
            "PATCH",
            f"/api/v1/automation/rules/{quote(rule_id, safe='')}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AutomationRuleResponse.model_validate(data)

    def delete_automation_rule(self, rule_id: str) -> None:
        self._request("DELETE", f"/api/v1/automation/rules/{quote(rule_id, safe='')}")

    def enable_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        return self.update_automation_rule(rule_id, AutomationRuleUpdate(enabled=True))

    def disable_automation_rule(self, rule_id: str) -> AutomationRuleResponse:
        return self.update_automation_rule(rule_id, AutomationRuleUpdate(enabled=False))

    def get_automation_stats(self) -> AutomationStatsResponse:
        data = self._request("GET", "/api/v1/automation/stats")
        return AutomationStatsResponse.model_validate(data)

    def list_automation_history(
        self,
        *,
        rule_id: str | None = None,
        source_device_id: str | None = None,
        status: str | None = None,
        conditions_met: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AutomationHistoryListResponse:
        params = {
            "rule_id": rule_id,
            "source_device_id": source_device_id,
            "status": status,
            "conditions_met": conditions_met,
            "limit": limit,
            "offset": offset,
        }
        data = self._request("GET", "/api/v1/automation/history", params={k: v for k, v in params.items() if v is not None})
        return AutomationHistoryListResponse.model_validate(data)

    def iter_automation_rules(
        self,
        *,
        enabled: bool | None = None,
        trigger_on: str | None = None,
        page_size: int = 100,
    ) -> Iterator[AutomationRuleResponse]:
        offset = 0
        while True:
            page = self.list_automation_rules(enabled=enabled, trigger_on=trigger_on, limit=page_size, offset=offset)
            for rule in page.rules:
                yield rule
            offset += len(page.rules)
            if offset >= page.total or not page.rules:
                break

    def iter_automation_history(
        self,
        *,
        rule_id: str | None = None,
        source_device_id: str | None = None,
        status: str | None = None,
        conditions_met: bool | None = None,
        page_size: int = 100,
    ) -> Iterator[AutomationHistoryResponse]:
        offset = 0
        while True:
            page = self.list_automation_history(
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
