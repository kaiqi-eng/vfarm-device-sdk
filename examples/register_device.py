from datetime import datetime, timezone

from vfarm_device_sdk import DeviceCreate, DeviceLocation, IngestDeviceInfo, IngestLocation, IngestReading, IngestRequest, ReadingValue, VFarmClient


def main() -> None:
    with VFarmClient(base_url="http://localhost:8000", api_key="change-me") as client:
        device = client.ensure_device(
            DeviceCreate(
                id="sdk-sensor-001",
                farm_id="farm-alpha",
                device_type="sensor",
                device_model="DHT22",
                firmware_version="1.0.0",
                location=DeviceLocation(rack_id="rack-a", node_id="node-7", position="top-left"),
                config={"sample_interval_seconds": 30},
                tags=["demo", "sdk"],
            )
        )
        print(device.model_dump_json(indent=2))

        reading = client.ingest(
            IngestRequest(
                sensor_id="sdk-sensor-001",
                sensor_type="DHT22",
                location=IngestLocation(farm_id="farm-alpha", rack_id="rack-a", node_id="node-7"),
                timestamp=datetime.now(timezone.utc),
                readings=IngestReading(
                    temperature=ReadingValue(value=23.4, unit="celsius", status="ok"),
                    humidity=ReadingValue(value=58.2, unit="percent_rh", status="ok"),
                ),
                device=IngestDeviceInfo(firmware="1.0.0", uptime_s=540, wifi_rssi=-48),
            )
        )
        print(reading.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
