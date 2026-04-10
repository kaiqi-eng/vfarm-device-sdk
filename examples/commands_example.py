from __future__ import annotations

from _common import get_sensor_type, make_client, unique_id
from vfarm_device_sdk import CommandAcknowledge, DeviceCreate, DeviceLocation


def main() -> None:
    farm_id = unique_id("sdk-example-farm")
    device_id = unique_id("sdk-example-cmd-device")

    with make_client() as client:
        client.ensure_farm(farm_id=farm_id, name="SDK Commands Example Farm")
        client.ensure_device(
            DeviceCreate(
                id=device_id,
                farm_id=farm_id,
                device_type="sensor",
                sensor_type_id=get_sensor_type(),
                device_model="DHT22",
                location=DeviceLocation(rack_id="rack-c", node_id="node-c", position="pc"),
                firmware_version="1.0.0",
            )
        )

        cmd = client.enqueue_restart_service(
            device_id,
            reason="commands example",
            delay_seconds=1,
            graceful=True,
        )
        print("created_command:", cmd.model_dump())

        pending = client.fetch_pending_commands(device_id, limit=10)
        print("pending_commands:", pending.model_dump())

        acked = client.update_command_status(
            device_id,
            cmd.id,
            CommandAcknowledge(status="acknowledged"),
        )
        print("acknowledged:", acked.model_dump())

        failed = client.update_command_status(
            device_id,
            cmd.id,
            CommandAcknowledge(status="failed", error_code="SIM_FAIL", error_message="Example failure"),
        )
        print("failed:", failed.model_dump())

        client.delete_device(device_id)
        client.delete_farm(farm_id)


if __name__ == "__main__":
    main()
