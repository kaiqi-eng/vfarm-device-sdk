from __future__ import annotations

import os
import uuid

from vfarm_device_sdk import VFarmClient


def get_base_url() -> str:
    return os.environ.get("SDK_BASE_URL", "http://localhost:8003").rstrip("/")


def get_api_key() -> str:
    key = os.environ.get("FARM_API_KEY")
    if not key:
        raise RuntimeError("FARM_API_KEY is required")
    return key


def get_sensor_type() -> str:
    return os.environ.get("SDK_SENSOR_TYPE", "dht22")


def unique_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def make_client() -> VFarmClient:
    return VFarmClient(base_url=get_base_url(), api_key=get_api_key())
