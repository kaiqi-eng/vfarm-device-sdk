from __future__ import annotations

from _common import get_sensor_type, make_client, unique_id
from vfarm_device_sdk import DeviceCreate, DeviceLocation, DeviceThresholdUpdate


def main() -> None:
    farm_id = unique_id("sdk-example-farm")
    device_id = unique_id("sdk-example-threshold-device")

    with make_client() as client:
        client.ensure_farm(farm_id=farm_id, name="SDK Thresholds Example Farm")
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=get_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-t", node_id="node-t", position="pt"),
                firmware_version="1.0.0",
            )
        )

        created = client.set_temperature_limits(
            device_id,
            min_c=18.0,
            max_c=30.0,
            severity="warning",
            cooldown_minutes=10,
            enabled=True,
        )
        print("set_temperature_limits:", created.model_dump())

        fetched = client.get_device_threshold(device_id, "temperature")
        print("get_temperature_threshold:", fetched.model_dump())

        updated = client.update_device_threshold(
            device_id,
            "temperature",
            DeviceThresholdUpdate(max_value=31.0, severity="error"),
        )
        print("updated_threshold:", updated.model_dump())

        listed = client.list_device_thresholds(device_id)
        print("list_thresholds:", listed.model_dump())

        client.delete_device_threshold(device_id, "temperature")
        client.delete_device(device_id)
        client.delete_farm(farm_id)


if __name__ == "__main__":
    main()
