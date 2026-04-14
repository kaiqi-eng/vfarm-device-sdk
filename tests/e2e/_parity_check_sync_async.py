from __future__ import annotations

import asyncio
import json
import os
import uuid

from vfarm_device_sdk import AsyncVFarmClient, DeviceCreate, DeviceLocation, VFarmClient


def main() -> None:
    base_url = os.environ["SDK_E2E_BASE_URL"]
    api_key = os.environ["FARM_API_KEY"]
    sensor_type = os.environ.get("SDK_E2E_SENSOR_TYPE", "dht22")

    suffix = uuid.uuid4().hex[:8]
    farm_id = f"sdk-parity-farm-{suffix}"
    device_id = f"sdk-parity-dev-{suffix}"

    report: list[dict[str, object]] = []
    samples: dict[str, object] = {}

    def ok(name: str, passed: bool, detail: str = "") -> None:
        report.append({"check": name, "passed": bool(passed), "detail": detail})

    with VFarmClient(base_url=base_url, api_key=api_key) as sync_client:
        sync_client.ensure_farm(farm_id=farm_id, name="SDK Parity Farm", description="sync/async parity")
        sync_client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-p", node_id="node-p", position="pp"),
                firmware_version="1.0.0",
            )
        )

        sync_health = sync_client.health()
        sync_farm = sync_client.get_farm(farm_id)
        sync_device = sync_client.get_device(device_id)
        cmd = sync_client.enqueue_set_value(device_id, target="fan-speed", value=41.0, unit="percent", reason="parity")
        sync_cmds = sync_client.list_device_commands(device_id, limit=20)
        sync_events = sync_client.get_device_events(device_id, limit=20)
        sync_ing = sync_client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type,
            farm_id=farm_id,
            rack_id="rack-p",
            node_id="node-p",
            firmware="1.0.0",
            temperature_value=24.2,
            humidity_value=56.4,
            uptime_s=120,
            wifi_rssi=-50,
            auto_register=False,
        )
        sync_latest = sync_client.get_latest_reading(device_id)
        sync_stats = sync_client.get_reading_stats(device_id, window="1h")

        samples["sync"] = {
            "health": sync_health,
            "farm": sync_farm.model_dump(mode="json"),
            "device": sync_device.model_dump(mode="json"),
            "command": cmd.model_dump(mode="json"),
            "ingest": sync_ing.model_dump(mode="json"),
            "latest": sync_latest.model_dump(mode="json"),
            "stats": sync_stats.model_dump(mode="json"),
            "events_count": sync_events.total,
            "commands_count": len(sync_cmds.commands),
        }

    async def run_async_checks() -> None:
        async with AsyncVFarmClient(base_url=base_url, api_key=api_key) as async_client:
            async_health = await async_client.health()
            async_farm = await async_client.get_farm(farm_id)
            async_device = await async_client.get_device(device_id)
            async_cmds = await async_client.list_device_commands(device_id, limit=20)
            async_events = await async_client.get_device_events(device_id, limit=20)
            async_latest = await async_client.get_latest_reading(device_id)
            async_stats = await async_client.get_reading_stats(device_id, window="1h")

            samples["async"] = {
                "health": async_health,
                "farm": async_farm.model_dump(mode="json"),
                "device": async_device.model_dump(mode="json"),
                "latest": async_latest.model_dump(mode="json"),
                "stats": async_stats.model_dump(mode="json"),
                "events_count": async_events.total,
                "commands_count": len(async_cmds.commands),
            }

            ok(
                "health.status",
                async_health.get("status") == samples["sync"]["health"].get("status"),  # type: ignore[index]
                f"sync={samples['sync']['health'].get('status')} async={async_health.get('status')}",  # type: ignore[index]
            )
            ok(
                "farm.identity",
                async_farm.id == samples["sync"]["farm"]["id"] and async_farm.name == samples["sync"]["farm"]["name"],  # type: ignore[index]
            )
            ok(
                "device.identity",
                async_device.id == samples["sync"]["device"]["id"] and async_device.farm_id == samples["sync"]["device"]["farm_id"],  # type: ignore[index]
            )
            ok(
                "device.sensor_type",
                async_device.sensor_type_id == samples["sync"]["device"]["sensor_type_id"],  # type: ignore[index]
            )
            ok(
                "commands.presence",
                len(async_cmds.commands) >= 1 and any(c.id == samples["sync"]["command"]["id"] for c in async_cmds.commands),  # type: ignore[index]
            )
            ok("events.nonempty", async_events.total >= 1 and samples["sync"]["events_count"] >= 1)  # type: ignore[index]
            ok(
                "latest.sensor_match",
                async_latest.sensor_id == samples["sync"]["latest"]["sensor_id"],  # type: ignore[index]
            )
            ok(
                "stats.window_match",
                async_stats.window == samples["sync"]["stats"]["window"],  # type: ignore[index]
            )
            ok(
                "stats.total_nonzero",
                async_stats.total_readings >= 1 and samples["sync"]["stats"]["total_readings"] >= 1,  # type: ignore[index]
            )

    asyncio.run(run_async_checks())

    print(json.dumps({"summary": report, "all_passed": all(x["passed"] for x in report), "samples": samples}, indent=2, default=str))


if __name__ == "__main__":
    main()
