from __future__ import annotations

from datetime import datetime, timezone

from _common import get_sensor_type, make_client, unique_id
from vfarm_device_sdk import DeviceCreate, DeviceLocation


def main() -> None:
    farm_id = unique_id("sdk-example-farm")
    device_id = unique_id("sdk-example-device")
    sensor_type = get_sensor_type()

    with make_client() as client:
        client.ensure_farm(
            farm_id=farm_id,
            name="SDK Device Example Farm",
            description="Created by register_device.py",
        )

        ensured = client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-a", node_id="node-1", position="p1"),
                firmware_version="1.0.0",
            )
        )
        print("ensure_device:", ensured.model_dump())

        ingest = client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type,
            farm_id=farm_id,
            rack_id="rack-a",
            node_id="node-1",
            firmware="1.0.0",
            temperature_value=24.2,
            humidity_value=54.1,
            timestamp=datetime.now(timezone.utc),
        )
        print("ingest_reading:", ingest.model_dump())

        latest = client.get_latest_reading(device_id)
        print("latest_reading:", latest.model_dump())

        client.delete_device(device_id)
        client.delete_farm(farm_id)


if __name__ == "__main__":
    main()
