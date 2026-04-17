from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from vfarm_device_sdk.async_ingestion import AsyncIngestionApiMixin
from vfarm_device_sdk.models import IngestRequest


def _run(coro):
    return asyncio.run(coro)


class _AsyncIngestionHarness(AsyncIngestionApiMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/api/v1/ingest":
            return {"id": 123, "received_at": datetime.now(timezone.utc).isoformat(), "processing_ms": 11}
        if method == "GET" and path == "/api/v1/health":
            return {"status": "ok"}
        raise AssertionError(f"Unhandled call {method} {path}")


def test_async_ingest_and_health() -> None:
    sdk = _AsyncIngestionHarness()
    payload = IngestRequest.model_validate(
        {
            "schema_version": "1.0.0",
            "sensor_id": "dev-1",
            "sensor_type": "dht22",
            "location": {"farm_id": "farm-a", "rack_id": "rack-1", "node_id": "node-1"},
            "readings": {
                "temperature": {"value": 24.1, "unit": "celsius", "status": "ok"},
                "humidity": {"value": 59.2, "unit": "percent_rh", "status": "ok"},
            },
            "device": {"firmware": "1.0.0"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    started = perf_counter()
    result = _run(sdk.ingest(payload))
    elapsed_ms = (perf_counter() - started) * 1000
    assert result.id == 123
    assert result.received_at is not None
    assert elapsed_ms >= 0.0

    health = _run(sdk.health())
    assert health["status"] == "ok"


def test_async_ingest_includes_idempotency_header_when_provided() -> None:
    sdk = _AsyncIngestionHarness()
    payload = IngestRequest.model_validate(
        {
            "schema_version": "1.0.0",
            "sensor_id": "dev-1",
            "sensor_type": "dht22",
            "location": {"farm_id": "farm-a", "rack_id": "rack-1", "node_id": "node-1"},
            "readings": {
                "temperature": {"value": 24.1, "unit": "celsius", "status": "ok"},
                "humidity": {"value": 59.2, "unit": "percent_rh", "status": "ok"},
            },
            "device": {"firmware": "1.0.0"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    _run(sdk.ingest(payload, idempotency_key="ingest-key-1"))
    _, _, kwargs = sdk.calls[0]
    assert kwargs["headers"]["Idempotency-Key"] == "ingest-key-1"


def test_async_ingest_reading_builds_payload() -> None:
    sdk = _AsyncIngestionHarness()
    result = _run(
        sdk.ingest_reading(
            sensor_id="dev-2",
            sensor_type="dht22",
            farm_id="farm-b",
            rack_id="rack-2",
            node_id="node-2",
            firmware="1.0.1",
            temperature_value=25.2,
            humidity_value=54.8,
            uptime_s=200,
            wifi_rssi=-50,
            auto_register=False,
        )
    )
    assert result.id == 123
    assert len(sdk.calls) >= 1
    method, path, kwargs = sdk.calls[0]
    assert method == "POST"
    assert path == "/api/v1/ingest"
    assert kwargs["json"]["sensor_id"] == "dev-2"
    assert kwargs["json"]["sensor_type"] == "dht22"


def test_async_ingest_reading_passes_idempotency_header() -> None:
    sdk = _AsyncIngestionHarness()
    _run(
        sdk.ingest_reading(
            sensor_id="dev-2",
            sensor_type="dht22",
            farm_id="farm-b",
            rack_id="rack-2",
            node_id="node-2",
            firmware="1.0.1",
            temperature_value=25.2,
            humidity_value=54.8,
            idempotency_key="ingest-key-2",
        )
    )

    _, _, kwargs = sdk.calls[0]
    assert kwargs["headers"]["Idempotency-Key"] == "ingest-key-2"
