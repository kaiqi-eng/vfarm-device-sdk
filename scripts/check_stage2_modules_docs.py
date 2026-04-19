from __future__ import annotations

import ast
import pathlib
import re
import sys

MODULES = (
    "core.py",
    "devices.py",
    "events.py",
    "thresholds.py",
    "device_capabilities.py",
    "ingestion.py",
    "readings.py",
)

RST_HEADER_CHARS = set("=-~`^\"'+*#")


def has_section(doc: str, name: str) -> bool:
    if re.search(r"(?im)^(?:#+\s*)?" + re.escape(name) + r"\s*:?\s*$", doc):
        return True

    lines = doc.splitlines()
    for i in range(len(lines) - 1):
        if lines[i].strip().lower() != name.lower():
            continue
        underline = lines[i + 1].strip()
        if len(underline) >= 3 and set(underline).issubset(RST_HEADER_CHARS):
            return True
    return False


def check_module(file_path: pathlib.Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    module_name = f"vfarm_device_sdk.{file_path.stem}"
    missing: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False) or ""
            if not doc.strip() or not has_section(doc, "Examples") or not has_section(doc, "Common Errors"):
                missing.append(f"{module_name}.{node.name}")
            continue

        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                doc = ast.get_docstring(member, clean=False) or ""
                qual = f"{module_name}.{node.name}.{member.name}"
                if not doc.strip() or not has_section(doc, "Examples") or not has_section(doc, "Common Errors"):
                    missing.append(qual)

    return missing


def main() -> int:
    base = pathlib.Path("python/vfarm_device_sdk")
    missing_all: list[str] = []

    for mod in MODULES:
        missing_all.extend(check_module(base / mod))

    print(f"Missing in stage2 modules: {len(missing_all)}")
    for item in missing_all:
        print(f" - {item}")

    return 1 if missing_all else 0


if __name__ == "__main__":
    raise SystemExit(main())

