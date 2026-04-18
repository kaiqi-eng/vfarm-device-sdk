from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = ROOT / "contracts" / "upstream_openapi_snapshot.json"
DEFAULT_CANDIDATE = ROOT / "contracts" / "upstream_openapi_candidate.json"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Missing OpenAPI file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _resolve_ref(doc: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not ref or not isinstance(ref, str) or not ref.startswith("#/"):
        return schema
    node: Any = doc
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, dict):
        return {}
    return node


def _type_set(schema: dict[str, Any]) -> set[str]:
    if "type" in schema and isinstance(schema["type"], str):
        return {schema["type"]}
    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        result: set[str] = set()
        for item in schema["anyOf"]:
            if isinstance(item, dict) and isinstance(item.get("type"), str):
                result.add(item["type"])
        return result
    return set()


def _schema_breaks(old_doc: dict[str, Any], new_doc: dict[str, Any], old: dict[str, Any], new: dict[str, Any], path: str) -> list[str]:
    issues: list[str] = []
    old_resolved = _resolve_ref(old_doc, old)
    new_resolved = _resolve_ref(new_doc, new)

    old_types = _type_set(old_resolved)
    new_types = _type_set(new_resolved)
    if old_types and new_types and not old_types.issubset(new_types):
        issues.append(f"{path}: type changed incompatibly ({old_types} -> {new_types})")
        return issues

    old_props = old_resolved.get("properties", {})
    new_props = new_resolved.get("properties", {})
    if isinstance(old_props, dict) and isinstance(new_props, dict):
        for key in old_resolved.get("required", []):
            if key not in new_props:
                issues.append(f"{path}: required property removed: {key}")
        for key, old_prop in old_props.items():
            if key not in new_props:
                continue
            if isinstance(old_prop, dict) and isinstance(new_props[key], dict):
                issues.extend(
                    _schema_breaks(
                        old_doc,
                        new_doc,
                        old_prop,
                        new_props[key],
                        f"{path}.properties.{key}",
                    )
                )

    old_items = old_resolved.get("items")
    new_items = new_resolved.get("items")
    if isinstance(old_items, dict) and isinstance(new_items, dict):
        issues.extend(_schema_breaks(old_doc, new_doc, old_items, new_items, f"{path}.items"))

    return issues


def _content_schema(op: dict[str, Any], status: str | None = None, *, request: bool = False) -> dict[str, Any] | None:
    if request:
        body = op.get("requestBody")
        if not isinstance(body, dict):
            return None
        content = body.get("content", {})
    else:
        responses = op.get("responses", {})
        if not isinstance(responses, dict):
            return None
        response = responses.get(status or "")
        if not isinstance(response, dict):
            return None
        content = response.get("content", {})
    if not isinstance(content, dict):
        return None
    app_json = content.get("application/json")
    if not isinstance(app_json, dict):
        return None
    schema = app_json.get("schema")
    return schema if isinstance(schema, dict) else None


def _check_breaking(old_doc: dict[str, Any], new_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    old_paths = old_doc.get("paths", {})
    new_paths = new_doc.get("paths", {})

    for path, old_ops in old_paths.items():
        if path not in new_paths:
            issues.append(f"Path removed: {path}")
            continue
        if not isinstance(old_ops, dict) or not isinstance(new_paths[path], dict):
            continue
        for method, old_op in old_ops.items():
            if method not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            new_op = new_paths[path].get(method)
            if not isinstance(new_op, dict):
                issues.append(f"Operation removed: {method.upper()} {path}")
                continue
            if not isinstance(old_op, dict):
                continue

            old_req_schema = _content_schema(old_op, request=True)
            new_req_schema = _content_schema(new_op, request=True)
            if old_req_schema and not new_req_schema:
                issues.append(f"Request body removed: {method.upper()} {path}")
            elif old_req_schema and new_req_schema:
                issues.extend(
                    _schema_breaks(
                        old_doc,
                        new_doc,
                        old_req_schema,
                        new_req_schema,
                        f"{method.upper()} {path} request",
                    )
                )

            old_responses = old_op.get("responses", {})
            new_responses = new_op.get("responses", {})
            if not isinstance(old_responses, dict) or not isinstance(new_responses, dict):
                continue
            for status, old_resp in old_responses.items():
                if status not in new_responses:
                    issues.append(f"Response status removed: {method.upper()} {path} [{status}]")
                    continue
                old_schema = _content_schema(old_op, status=status, request=False)
                new_schema = _content_schema(new_op, status=status, request=False)
                if old_schema and not new_schema:
                    issues.append(f"JSON response schema removed: {method.upper()} {path} [{status}]")
                elif old_schema and new_schema:
                    issues.extend(
                        _schema_breaks(
                            old_doc,
                            new_doc,
                            old_schema,
                            new_schema,
                            f"{method.upper()} {path} response[{status}]",
                        )
                    )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenAPI candidate for breaking changes.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    args = parser.parse_args()

    baseline = _load(args.baseline)
    candidate = _load(args.candidate)
    issues = _check_breaking(baseline, candidate)
    if issues:
        print("Breaking OpenAPI drift detected:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("OpenAPI breaking check passed (additive changes allowed).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
