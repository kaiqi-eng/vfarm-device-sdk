from __future__ import annotations

from _common import get_sensor_type, make_client, unique_id
from vfarm_device_sdk import DeviceCreate, DeviceLocation


def main() -> None:
    farm_id = unique_id("sdk-example-farm")
    device_id = unique_id("sdk-example-reading-device")
    sensor_type = get_sensor_type()

    with make_client() as client:
        client.ensure_farm(farm_id=farm_id, name="SDK Readings Example Farm")
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=sensor_type,
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-r", node_id="node-r", position="pr"),
                firmware_version="1.0.0",
            )
        )

        client.ingest_reading(
            sensor_id=device_id,
            sensor_type=sensor_type,
            farm_id=farm_id,
            rack_id="rack-r",
            node_id="node-r",
            firmware="1.0.0",
            temperature_value=24.3,
            humidity_value=56.2,
            uptime_s=120,
            wifi_rssi=-45,
        )

        latest = client.get_latest_reading(device_id)
        print("latest:", latest.model_dump())

        history = client.list_readings(device_id, limit=20)
        print("history_count:", history.count)

        stats = client.get_reading_stats(device_id, window="1h")
        print("stats:", stats.model_dump())

        snapshot = client.get_readings_analytics(device_id, window="1h", recent_limit=20)
        print("analytics_snapshot:", snapshot.model_dump())

        client.delete_device(device_id)
        client.delete_farm(farm_id)


if __name__ == "__main__":
    main()
