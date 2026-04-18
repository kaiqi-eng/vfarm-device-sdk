from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script(module_name: str):
    root = Path(__file__).resolve().parents[2]
    script_path = root / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script module: {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_openapi_breaking_allows_additive_changes() -> None:
    breaking = _load_script("check_openapi_breaking")
    baseline = {
        "paths": {
            "/api/v1/test": {
                "post": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["id"],
                                        "properties": {"id": {"type": "string"}},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    candidate = {
        "paths": {
            "/api/v1/test": {
                "post": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["id"],
                                        "properties": {
                                            "id": {"type": "string"},
                                            "extra": {"type": "string"},
                                        },
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert breaking._check_breaking(baseline, candidate) == []


def test_openapi_breaking_flags_removed_required_field() -> None:
    breaking = _load_script("check_openapi_breaking")
    baseline = {
        "paths": {
            "/api/v1/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name"],
                                        "properties": {"name": {"type": "string"}},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    candidate = {
        "paths": {
            "/api/v1/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "properties": {"other": {"type": "string"}}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    issues = breaking._check_breaking(baseline, candidate)
    assert any("required property removed" in issue for issue in issues)


def test_sdk_openapi_compat_handles_nullable_union_with_ref() -> None:
    compat = _load_script("check_sdk_openapi_compat")
    sdk_schema = {
        "type": "object",
        "properties": {
            "temperature": {
                "anyOf": [
                    {"$ref": "#/$defs/ReadingValue"},
                    {"type": "null"},
                ]
            }
        },
        "$defs": {"ReadingValue": {"type": "object", "properties": {"value": {"type": "number"}}}},
    }
    openapi = {
        "components": {
            "schemas": {
                "ReadingValue": {"type": "object", "properties": {"value": {"type": "number"}}}
            }
        }
    }
    issues = compat._schema_compatible(
        sdk_schema,
        openapi,
        sdk_schema["properties"]["temperature"],
        {"$ref": "#/components/schemas/ReadingValue"},
        "Ingest request.temperature",
    )
    assert issues == []
