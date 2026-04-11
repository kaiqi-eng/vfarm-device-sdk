from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DeviceType = Literal["gateway", "sensor", "controller", "actuator"]
DeviceStatus = Literal["online", "offline", "maintenance", "error", "unknown"]
ReadingStatus = Literal["ok", "error"]
StatsWindow = Literal["1h", "6h", "24h", "7d", "30d"]


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


class DeviceHeartbeatResponse(BaseModel):
    device_id: str
    last_seen: datetime
    status: DeviceStatus | str


class DeviceBatchCreateItem(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9\-_]+$", min_length=1, max_length=64)
    farm_id: str = Field(min_length=1, max_length=64)
    device_type: DeviceType = "sensor"
    tags: list[str] = Field(default_factory=list)


class DeviceBatchRegisterResponse(BaseModel):
    created: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


class DeviceMetadataResponse(BaseModel):
    device_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class DeviceMetadataUpdateResponse(BaseModel):
    device_id: str
    config: dict[str, Any] = Field(default_factory=dict)


class DeviceEventResponse(BaseModel):
    id: int
    device_id: str
    event_type: str
    event_category: str
    severity: str
    event_data: dict[str, Any] | None = None
    previous_state: dict[str, Any] | None = None
    source: str | None = None
    correlation_id: str | None = None
    occurred_at: datetime


class DeviceEventsListResponse(BaseModel):
    device_id: str
    events: list[DeviceEventResponse]
    total: int


class DeviceThresholdCreate(BaseModel):
    metric: str = Field(min_length=1, max_length=32)
    min_value: float | None = None
    max_value: float | None = None
    severity: Literal["warning", "error", "critical"] = "warning"
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)
    enabled: bool = True


class DeviceThresholdUpdate(BaseModel):
    min_value: float | None = None
    max_value: float | None = None
    severity: Literal["warning", "error", "critical"] | None = None
    cooldown_minutes: int | None = Field(default=None, ge=1, le=1440)
    enabled: bool | None = None


class DeviceThresholdResponse(BaseModel):
    id: str
    device_id: str
    metric: str
    min_value: float | None = None
    max_value: float | None = None
    severity: str
    cooldown_minutes: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class DeviceThresholdListResponse(BaseModel):
    device_id: str
    thresholds: list[DeviceThresholdResponse]
    total: int


class DeviceCapabilityCreate(BaseModel):
    capability_id: str = Field(min_length=1, max_length=32)
    calibration_offset: float = 0.0
    calibration_scale: float = Field(default=1.0, gt=0)
    custom_min: float | None = None
    custom_max: float | None = None
    enabled: bool = True
    notes: str | None = None


class DeviceCapabilityUpdate(BaseModel):
    calibration_offset: float | None = None
    calibration_scale: float | None = Field(default=None, gt=0)
    custom_min: float | None = None
    custom_max: float | None = None
    enabled: bool | None = None
    notes: str | None = None


class DeviceCapabilityResponse(BaseModel):
    device_id: str
    capability_id: str
    capability_name: str
    category: str
    data_type: str
    unit: str | None = None
    unit_symbol: str | None = None
    base_min_value: float | None = None
    base_max_value: float | None = None
    calibration_offset: float
    calibration_scale: float
    custom_min: float | None = None
    custom_max: float | None = None
    effective_min: float | None = None
    effective_max: float | None = None
    enabled: bool
    last_calibrated_at: datetime | None = None
    notes: str | None = None
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DeviceCapabilityListResponse(BaseModel):
    device_id: str
    sensor_type_id: str | None = None
    capabilities: list[DeviceCapabilityResponse]
    total: int


SensorTypeCommunication = Literal["i2c", "spi", "uart", "onewire", "analog", "digital", "modbus", "rs485"]


class SensorTypeCapabilityCreate(BaseModel):
    capability_id: str = Field(min_length=1, max_length=32)
    is_primary: bool = True
    accuracy: str | None = Field(default=None, max_length=32)
    resolution: str | None = Field(default=None, max_length=32)
    sample_rate_hz: float | None = Field(default=None, ge=0)
    notes: str | None = None


class SensorTypeCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    manufacturer: str | None = Field(default=None, max_length=64)
    description: str | None = None
    datasheet_url: str | None = None
    communication: SensorTypeCommunication | None = None
    power_voltage: str | None = Field(default=None, max_length=16)
    capabilities: list[SensorTypeCapabilityCreate] = Field(default_factory=list)


class SensorTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    manufacturer: str | None = Field(default=None, max_length=64)
    description: str | None = None
    datasheet_url: str | None = None
    communication: SensorTypeCommunication | None = None
    power_voltage: str | None = Field(default=None, max_length=16)
    is_active: bool | None = None


class SensorTypeCapabilityResponse(BaseModel):
    capability_id: str
    capability_name: str
    capability_unit: str | None = None
    capability_unit_symbol: str | None = None
    is_primary: bool
    accuracy: str | None = None
    resolution: str | None = None
    sample_rate_hz: float | None = None
    notes: str | None = None


class SensorTypeResponse(BaseModel):
    id: str
    name: str
    manufacturer: str | None = None
    description: str | None = None
    datasheet_url: str | None = None
    communication: str | None = None
    power_voltage: str | None = None
    capabilities: list[SensorTypeCapabilityResponse] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SensorTypeListResponse(BaseModel):
    sensor_types: list[SensorTypeResponse]
    total: int


CapabilityCategory = Literal["environmental", "network", "power", "actuator"]
CapabilityDataType = Literal["numeric", "boolean", "string"]


class CapabilityCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    category: CapabilityCategory
    data_type: CapabilityDataType
    unit: str | None = Field(default=None, max_length=16)
    unit_symbol: str | None = Field(default=None, max_length=8)
    min_value: float | None = None
    max_value: float | None = None
    precision: int = Field(default=2, ge=0, le=6)
    icon: str | None = Field(default=None, max_length=32)


class CapabilityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    category: CapabilityCategory | None = None
    data_type: CapabilityDataType | None = None
    unit: str | None = Field(default=None, max_length=16)
    unit_symbol: str | None = Field(default=None, max_length=8)
    min_value: float | None = None
    max_value: float | None = None
    precision: int | None = Field(default=None, ge=0, le=6)
    icon: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None


class CapabilityResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str
    data_type: str
    unit: str | None = None
    unit_symbol: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    precision: int
    icon: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CapabilityListResponse(BaseModel):
    capabilities: list[CapabilityResponse]
    total: int


class CapabilityGroupCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=32)
    display_order: int = Field(default=100, ge=0)
    capability_ids: list[str] = Field(default_factory=list)


class CapabilityGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=32)
    display_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class CapabilityGroupMemberResponse(BaseModel):
    capability_id: str
    capability_name: str
    category: str
    data_type: str
    unit: str | None = None
    unit_symbol: str | None = None
    display_order: int


class CapabilityGroupResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    icon: str | None = None
    display_order: int
    capabilities: list[CapabilityGroupMemberResponse] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CapabilityGroupListResponse(BaseModel):
    groups: list[CapabilityGroupResponse]
    total: int


class FarmCreate(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*$", min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    address: str | None = None


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    address: str | None = None
    is_active: bool | None = None


class FarmResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    address: str | None = None
    is_active: bool
    device_count: int = 0
    created_at: datetime
    updated_at: datetime


class FarmListResponse(BaseModel):
    farms: list[FarmResponse]
    total: int


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


class ReadingRecordResponse(BaseModel):
    id: int
    sensor_id: str
    reading_ts: datetime
    received_at: datetime
    temperature_c: float | None = None
    temperature_status: str
    humidity_rh: float | None = None
    humidity_status: str
    firmware: str
    uptime_s: int | None = None
    wifi_rssi: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class LatestReadingResponse(ReadingRecordResponse):
    pass


class ReadingsListResponse(BaseModel):
    sensor_id: str
    from_: datetime = Field(alias="from")
    to: datetime
    count: int
    readings: list[ReadingRecordResponse]

    model_config = {"populate_by_name": True}


class TemperatureStatsValues(BaseModel):
    min_c: float | None = None
    max_c: float | None = None
    avg_c: float | None = None


class HumidityStatsValues(BaseModel):
    min_rh: float | None = None
    max_rh: float | None = None
    avg_rh: float | None = None


class ReadingStatsResponse(BaseModel):
    sensor_id: str
    window: StatsWindow | str
    from_: datetime = Field(alias="from")
    to: datetime
    total_readings: int
    error_readings: int
    temperature: TemperatureStatsValues
    humidity: HumidityStatsValues

    model_config = {"populate_by_name": True}


class ReadingAnalyticsSnapshot(BaseModel):
    sensor_id: str
    latest: LatestReadingResponse | None = None
    recent: ReadingsListResponse
    stats: ReadingStatsResponse


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
