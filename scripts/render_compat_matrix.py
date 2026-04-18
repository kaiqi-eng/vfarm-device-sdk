from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "contracts" / "sdk_compatibility_matrix.json"
DOC_PATH = ROOT / "docs" / "SDK_COMPATIBILITY.md"


def _load_matrix() -> dict[str, Any]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8-sig"))


def _render_table(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# SDK Compatibility Matrix",
        "",
        "Source of truth: `contracts/sdk_compatibility_matrix.json`.",
        "",
        "| SDK Version | SDK Tag | vfarm API Ref/Tag | Contract Status | Verified At | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in entries:
        lines.append(
            "| {sdk_version} | {sdk_tag} | {vfarm_api_ref} | {contract_status} | {verified_at} | {notes} |".format(
                sdk_version=row.get("sdk_version", ""),
                sdk_tag=row.get("sdk_tag", ""),
                vfarm_api_ref=row.get("vfarm_api_ref", ""),
                contract_status=row.get("contract_status", ""),
                verified_at=row.get("verified_at", ""),
                notes=str(row.get("notes", "")).replace("|", "/"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    payload = _load_matrix()
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        raise RuntimeError("Invalid matrix payload; 'entries' must be a list.")
    rendered = _render_table(entries)
    DOC_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Rendered compatibility matrix: {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
