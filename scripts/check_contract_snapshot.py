from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from vfarm_device_sdk import models


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = ROOT / "contracts" / "sdk_model_schema_snapshot.json"


def _collect_model_schemas() -> dict[str, Any]:
    schemas: dict[str, Any] = {}
    for name in dir(models):
        obj = getattr(models, name)
        if not isinstance(obj, type):
            continue
        if not issubclass(obj, BaseModel):
            continue
        if obj.__module__ != models.__name__:
            continue
        schemas[name] = obj.model_json_schema(mode="validation")
    return dict(sorted(schemas.items()))


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _build_current_payload() -> dict[str, Any]:
    return {
        "snapshot_version": 1,
        "models": _collect_model_schemas(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SDK model schemas against snapshot.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Rewrite the snapshot file with the current schemas.",
    )
    args = parser.parse_args()

    current = _build_current_payload()

    if args.update:
        _write_json(SNAPSHOT_PATH, current)
        print(f"Updated snapshot: {SNAPSHOT_PATH}")
        return 0

    if not SNAPSHOT_PATH.exists():
        print(f"Missing snapshot file: {SNAPSHOT_PATH}")
        print("Run: python scripts/check_contract_snapshot.py --update")
        return 1

    expected = _load_json(SNAPSHOT_PATH)
    if current != expected:
        print("SDK model schema snapshot drift detected.")
        print("Run: python scripts/check_contract_snapshot.py --update")
        return 1

    print("SDK model schema snapshot check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
