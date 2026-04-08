from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DeviceType = Literal["gateway", "sensor", "controller", "actuator"]
DeviceStatus = Literal["online", "offline", "maintenance", "error", "unknown"]
ReadingStatus = Literal["ok", "error"]


class DeviceLocation(BaseModel):
    rack_id: str | None = Field(default=None, max_length=32)
    node_id: str | None = Field(default=None, max_length=32)
    position: str | None = Field(default=None, max_length=32)


class DeviceCreate(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9\-_]+$", min_length=1, max_length=64)
    farm_id: str = Field(min_length=1, max_length=64)
    device_type: DeviceType
    device_model: str | None = Field(default=None, max_length=32)
    sensor_type_id: str | None = Field(default=None, max_length=32)
    parent_device_id: str | None = Field(default=None, max_length=64)
    location: DeviceLocation | None = None
    capabilities: list[str] = Field(default_factory=list)
    firmware_version: str | None = Field(default=None, max_length=16)
    hardware_revision: str | None = Field(default=None, max_length=16)
    mac_address: str | None = Field(default=None, pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    ip_address: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class DeviceUpdate(BaseModel):
    farm_id: str | None = Field(default=None, min_length=1, max_length=64)
    device_model: str | None = Field(default=None, max_length=32)
    sensor_type_id: str | None = Field(default=None, max_length=32)
    parent_device_id: str | None = Field(default=None, max_length=64)
    location: DeviceLocation | None = None
    capabilities: list[str] | None = None
    firmware_version: str | None = Field(default=None, max_length=16)
    hardware_revision: str | None = Field(default=None, max_length=16)
    mac_address: str | None = Field(default=None, pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    ip_address: str | None = None
    config: dict[str, Any] | None = None
    calibration_data: dict[str, Any] | None = None
    tags: list[str] | None = None
    notes: str | None = None
    status: Literal["online", "offline", "maintenance", "error"] | None = None


class DeviceCreatedResponse(BaseModel):
    id: str
    created_at: datetime


class DeviceResponse(BaseModel):
    id: str
    device_type: str
    device_model: str | None = None
    sensor_type_id: str | None = None
    parent_device_id: str | None = None
    child_device_count: int = 0
    farm_id: str
    rack_id: str | None = None
    node_id: str | None = None
    position: str | None = None
    status: DeviceStatus | str
    health_score: int | None = None
    last_seen_at: datetime | None = None
    last_reading_at: datetime | None = None
    current_state: dict[str, Any] | None = None
    capabilities: list[str] = Field(default_factory=list)
    firmware_version: str | None = None
    hardware_revision: str | None = None
    mac_address: str | None = None
    ip_address: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    calibration_data: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    installed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    total: int
    online_count: int
    offline_count: int
    registered_count: int
    maintenance_count: int
    error_count: int
    unhealthy_count: int


class EnsureDeviceResult(BaseModel):
    created: bool
    device: DeviceResponse
    created_response: DeviceCreatedResponse | None = None


class ReadingValue(BaseModel):
    value: float | int | None = None
    unit: str
    status: ReadingStatus


class IngestLocation(BaseModel):
    farm_id: str
    rack_id: str
    node_id: str


class IngestDeviceInfo(BaseModel):
    firmware: str
    uptime_s: int | None = None
    wifi_rssi: int | None = None


class IngestErrorInfo(BaseModel):
    code: str
    message: str


class IngestReading(BaseModel):
    temperature: ReadingValue | None = None
    humidity: ReadingValue | None = None


class IngestRequest(BaseModel):
    schema_version: str = "1.0.0"
    sensor_id: str
    sensor_type: str
    location: IngestLocation
    timestamp: datetime
    readings: IngestReading
    device: IngestDeviceInfo
    error: IngestErrorInfo | None = None


class IngestResponse(BaseModel):
    id: int
    received_at: datetime


CommandType = Literal["config_update", "restart_service", "set_state", "set_value", "custom"]
CommandStatus = Literal[
    "pending",
    "delivered",
    "acknowledged",
    "completed",
    "failed",
    "expired",
    "cancelled",
]


class ConfigUpdatePayload(BaseModel):
    changes: dict[str, Any] = Field(default_factory=dict)
    merge_strategy: Literal["patch", "replace"] = "patch"


class RestartServicePayload(BaseModel):
    reason: str | None = None
    delay_seconds: int = Field(default=5, ge=0, le=300)
    graceful: bool = True


class SetStatePayload(BaseModel):
    target: str
    state: Literal["on", "off"]
    reason: str | None = None


class SetValuePayload(BaseModel):
    target: str
    value: float
    unit: str | None = None
    reason: str | None = None


class CustomPayload(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class CommandCreate(BaseModel):
    command_type: CommandType
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=100, ge=1, le=1000)
    ttl_minutes: int = Field(default=60, ge=5, le=1440)
    notes: str | None = None


class CommandAcknowledge(BaseModel):
    status: Literal["acknowledged", "completed", "failed"]
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


class CommandResponse(BaseModel):
    id: str
    device_id: str
    command_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int
    status: str
    created_at: datetime
    expires_at: datetime
    delivered_at: datetime | None = None
    acknowledged_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_by: str | None = None
    notes: str | None = None
    automation_rule_id: str | None = None


class CommandListResponse(BaseModel):
    device_id: str
    commands: list[CommandResponse]
    total: int
    pending_count: int


class PendingCommandsResponse(BaseModel):
    device_id: str
    commands: list[CommandResponse]
    poll_again_seconds: int = 30
