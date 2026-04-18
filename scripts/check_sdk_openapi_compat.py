from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from vfarm_device_sdk import models


ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "contracts" / "upstream_openapi_candidate.json"
MAPPING_PATH = ROOT / "contracts" / "sdk_openapi_mapping.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _resolve_ref(doc: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return schema
    node: Any = doc
    for part in ref[2:].split("/"):
        node = node[part]
    return node if isinstance(node, dict) else {}


def _component_schema(openapi: dict[str, Any], name: str) -> dict[str, Any]:
    schemas = openapi.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict) or name not in schemas or not isinstance(schemas[name], dict):
        raise RuntimeError(f"OpenAPI component not found: {name}")
    return schemas[name]


def _operation_exists(openapi: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    paths = openapi.get("paths", {})
    if path not in paths or not isinstance(paths[path], dict):
        raise RuntimeError(f"OpenAPI path missing: {path}")
    op = paths[path].get(method)
    if not isinstance(op, dict):
        raise RuntimeError(f"OpenAPI operation missing: {method.upper()} {path}")
    return op


def _type_set(root: dict[str, Any], schema: dict[str, Any]) -> set[str]:
    resolved = _resolve_ref(root, schema)
    result: set[str] = set()
    node_type = resolved.get("type")
    if isinstance(node_type, str):
        result.add(node_type)
    for key in ("anyOf", "oneOf", "allOf"):
        variants = resolved.get(key)
        if not isinstance(variants, list):
            continue
        for item in variants:
            if isinstance(item, dict):
                result.update(_type_set(root, item))
    return result


def _schema_compatible(
    sdk_root: dict[str, Any],
    openapi_root: dict[str, Any],
    sdk_schema: dict[str, Any],
    openapi_schema: dict[str, Any],
    path: str,
) -> list[str]:
    issues: list[str] = []
    sdk_resolved = _resolve_ref(sdk_root, sdk_schema)
    openapi_resolved = _resolve_ref(openapi_root, openapi_schema)

    sdk_types = _type_set(sdk_root, sdk_resolved)
    openapi_types = _type_set(openapi_root, openapi_resolved)
    if sdk_types and openapi_types and sdk_types.isdisjoint(openapi_types):
        issues.append(f"{path}: incompatible types sdk={sdk_types}, openapi={openapi_types}")
        return issues

    sdk_props = sdk_resolved.get("properties", {})
    openapi_props = openapi_resolved.get("properties", {})
    if isinstance(sdk_props, dict) and isinstance(openapi_props, dict):
        for key in sdk_resolved.get("required", []):
            if key not in openapi_props:
                issues.append(f"{path}: required SDK field missing in OpenAPI: {key}")
        for key, sdk_prop in sdk_props.items():
            if key not in openapi_props:
                continue
            if isinstance(sdk_prop, dict) and isinstance(openapi_props[key], dict):
                issues.extend(
                    _schema_compatible(
                        sdk_root,
                        openapi_root,
                        sdk_prop,
                        openapi_props[key],
                        f"{path}.properties.{key}",
                    )
                )
    return issues


def _model_schema(model_name: str) -> dict[str, Any]:
    model = getattr(models, model_name, None)
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        raise RuntimeError(f"SDK model not found: {model_name}")
    return model.model_json_schema(mode="validation")


def _operation_component_matches(openapi: dict[str, Any], op: dict[str, Any], direction: str, status: str | None, expected: str) -> None:
    if direction == "request":
        req = op.get("requestBody", {})
        schema = req.get("content", {}).get("application/json", {}).get("schema", {})
    else:
        resp = op.get("responses", {}).get(status or "", {})
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
    if not isinstance(schema, dict):
        raise RuntimeError("Expected JSON schema missing in operation mapping.")
    resolved = _resolve_ref(openapi, schema)
    expected_schema = _component_schema(openapi, expected)
    if resolved != expected_schema:
        raise RuntimeError(
            f"Mapped component mismatch. Expected operation schema to resolve to '{expected}'."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SDK model compatibility with mapped OpenAPI components.")
    parser.add_argument("--openapi", type=Path, default=OPENAPI_PATH)
    parser.add_argument("--mapping", type=Path, default=MAPPING_PATH)
    args = parser.parse_args()

    openapi = _load_json(args.openapi)
    mapping = _load_json(args.mapping)
    checks = mapping.get("checks", [])
    if not isinstance(checks, list):
        raise RuntimeError("Invalid mapping file: 'checks' must be a list.")

    issues: list[str] = []
    for row in checks:
        name = row["name"]
        path = row["path"]
        method = row["method"]
        direction = row["direction"]
        status = row.get("status")
        openapi_component = row["openapi_component"]
        sdk_model_name = row["sdk_model"]

        try:
            op = _operation_exists(openapi, path, method)
            _operation_component_matches(openapi, op, direction, status, openapi_component)
            openapi_schema = _component_schema(openapi, openapi_component)
            sdk_schema = _model_schema(sdk_model_name)
            issues.extend(_schema_compatible(sdk_schema, openapi, sdk_schema, openapi_schema, name))
        except RuntimeError as exc:
            issues.append(f"{name}: {exc}")

    if issues:
        print("SDK/OpenAPI compatibility issues detected:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("SDK/OpenAPI compatibility check passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
