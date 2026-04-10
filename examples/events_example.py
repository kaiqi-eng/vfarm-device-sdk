from __future__ import annotations

from itertools import islice

from _common import get_sensor_type, make_client, unique_id
from vfarm_device_sdk import CommandCreate, DeviceCreate, DeviceLocation


def main() -> None:
    farm_id = unique_id("sdk-example-farm")
    device_id = unique_id("sdk-example-events-device")

    with make_client() as client:
        client.ensure_farm(farm_id=farm_id, name="SDK Events Example Farm")
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=get_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-e", node_id="node-e", position="pe"),
                firmware_version="1.0.0",
            )
        )

        created = client.create_command(
            device_id,
            CommandCreate(
                command_type="restart_service",
                payload={"reason": "events example", "delay_seconds": 1, "graceful": True},
                priority=100,
                ttl_minutes=30,
            ),
        )
        print("trigger_command:", created.model_dump())

        events = client.get_device_events(device_id, limit=20)
        print("events_page:", events.model_dump())

        latest = client.get_latest_device_event(device_id)
        print("latest_event:", latest.model_dump() if latest else None)

        first_two = list(islice(client.iter_device_events(device_id, page_size=5), 2))
        print("iter_first_two:", [e.model_dump() for e in first_two])

        client.delete_device(device_id)
        client.delete_farm(farm_id)


if __name__ == "__main__":
    main()
