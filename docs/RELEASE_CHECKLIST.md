# Release Checklist

Manual release flow is enforced by CI/publish guard scripts.

## Before creating a release

1. Update `pyproject.toml` `project.version`.
2. Add a matching entry in `CHANGELOG.md`.
3. Update `contracts/sdk_compatibility_matrix.json` with the new SDK version and vfarm API ref/tag.
4. Refresh `contracts/upstream_openapi_candidate.json` from upstream OpenAPI and run:
   - `python scripts/check_openapi_breaking.py`
   - `python scripts/check_sdk_openapi_compat.py`
5. If candidate changes are approved as new baseline, copy candidate to `contracts/upstream_openapi_snapshot.json`.
6. Re-run local checks:
   - `python scripts/check_contract_snapshot.py`
   - `pytest -q tests/unit`

## TestPyPI publish

1. Trigger **Publish to TestPyPI** workflow.
2. Workflow runs `scripts/release_guard.py --target testpypi`.
3. If guard fails due version reuse, bump version and repeat.

## PyPI publish

1. Create and push tag `v<version>` (must match `pyproject.toml`).
2. Publish GitHub release for that tag.
3. Workflow runs `scripts/release_guard.py --target pypi --require-tag --tag <release-tag>`.
4. Verify package on PyPI and update release notes if needed.
