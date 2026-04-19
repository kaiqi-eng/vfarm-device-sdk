from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys
from dataclasses import dataclass


SECTION_RE_TEMPLATE = r"(?im)^(?:#+\s*)?{name}\s*:?\s*$"
RST_HEADER_CHARS = set("=-~`^\"'+*#")


@dataclass(frozen=True)
class FunctionDocCheck:
    qualified_name: str
    has_docstring: bool
    has_examples: bool
    has_common_errors: bool


def _iter_python_files(package_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted(path for path in package_dir.rglob("*.py") if path.is_file())


def _module_name_from_path(package_dir: pathlib.Path, file_path: pathlib.Path) -> str:
    relative = file_path.relative_to(package_dir.parent)
    return ".".join(relative.with_suffix("").parts)


def _has_named_section(docstring: str, section_name: str) -> bool:
    name = re.escape(section_name)
    if re.search(SECTION_RE_TEMPLATE.format(name=name), docstring):
        return True

    lines = docstring.splitlines()
    for index, line in enumerate(lines[:-1]):
        if line.strip().lower() != section_name.lower():
            continue
        underline = lines[index + 1].strip()
        if len(underline) >= 3 and set(underline).issubset(RST_HEADER_CHARS):
            return True
    return False


def _collect_function_checks(file_path: pathlib.Path, module_name: str) -> list[FunctionDocCheck]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    checks: list[FunctionDocCheck] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            checks.append(_build_check(module_name, node.name, ast.get_docstring(node, clean=False)))
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified_name = f"{module_name}.{node.name}.{member.name}"
                    checks.append(_build_check(qualified_name, None, ast.get_docstring(member, clean=False)))

    return checks


def _build_check(prefix: str, function_name: str | None, docstring: str | None) -> FunctionDocCheck:
    qualified_name = f"{prefix}.{function_name}" if function_name else prefix
    has_docstring = bool(docstring and docstring.strip())
    if not has_docstring:
        return FunctionDocCheck(
            qualified_name=qualified_name,
            has_docstring=False,
            has_examples=False,
            has_common_errors=False,
        )
    return FunctionDocCheck(
        qualified_name=qualified_name,
        has_docstring=True,
        has_examples=_has_named_section(docstring, "Examples"),
        has_common_errors=_has_named_section(docstring, "Common Errors"),
    )


def run(package_dir: pathlib.Path) -> int:
    all_checks: list[FunctionDocCheck] = []
    for file_path in _iter_python_files(package_dir):
        module_name = _module_name_from_path(package_dir, file_path)
        all_checks.extend(_collect_function_checks(file_path, module_name))

    missing_docstring = sorted(c.qualified_name for c in all_checks if not c.has_docstring)
    missing_examples = sorted(c.qualified_name for c in all_checks if c.has_docstring and not c.has_examples)
    missing_common_errors = sorted(c.qualified_name for c in all_checks if c.has_docstring and not c.has_common_errors)

    total = len(all_checks)
    print(f"Checked {total} functions/methods in {package_dir}")
    print(f"Missing docstring: {len(missing_docstring)}")
    print(f"Missing Examples section: {len(missing_examples)}")
    print(f"Missing Common Errors section: {len(missing_common_errors)}")

    if not (missing_docstring or missing_examples or missing_common_errors):
        print("Documentation completeness check passed.")
        return 0

    if missing_docstring:
        print("\nFunctions missing docstrings:")
        for name in missing_docstring:
            print(f"  - {name}")

    if missing_examples:
        print("\nFunctions missing Examples section:")
        for name in missing_examples:
            print(f"  - {name}")

    if missing_common_errors:
        print("\nFunctions missing Common Errors section:")
        for name in missing_common_errors:
            print(f"  - {name}")

    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail if any function/method in the SDK package is missing a docstring, "
            "an Examples section, or a Common Errors section."
        )
    )
    parser.add_argument(
        "--package-dir",
        default="python/vfarm_device_sdk",
        help="Path to package directory to validate (default: python/vfarm_device_sdk).",
    )
    args = parser.parse_args()

    package_dir = pathlib.Path(args.package_dir).resolve()
    if not package_dir.exists():
        print(f"Package directory does not exist: {package_dir}", file=sys.stderr)
        return 2
    if not package_dir.is_dir():
        print(f"Package directory is not a directory: {package_dir}", file=sys.stderr)
        return 2

    return run(package_dir)


if __name__ == "__main__":
    raise SystemExit(main())

