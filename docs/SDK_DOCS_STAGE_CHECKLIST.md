# SDK Docs Stage Checklist

Objective acceptance criteria for each rollout stage in `docs/SDK_DOCS_PLAN.md`.

## Stage 1: Foundation + Enforcement

- [x] `docs-site/` exists with Sphinx config and API toctree.
- [x] Docs tooling is installed via dev extras.
- [x] `scripts/check_docs_completeness.py` exists and runs.
- [x] Standard function docstring template is defined.

## Stage 2: Sync Surface (Part A)

- [x] Modules covered: `core`, `devices`, `events`, `thresholds`, `device_capabilities`, `ingestion`, `readings`.
- [x] Functions include `Examples` and `Common Errors`.
- [x] Stage checker passes (`scripts/check_stage2_modules_docs.py`).

## Stage 3: Sync Surface (Part B) + Error Matrix

- [x] Modules covered: `commands`, `farms`, `sensor_types`, `capabilities`, `capability_groups`, `automation`, `alerts`, `idempotency`, `exceptions`, `client`.
- [x] Endpoint and helper error behavior is documented.
- [x] Error-code reference pages exist under `docs-site/error_codes/`.
- [x] Stage checker passes (`scripts/check_stage3_modules_docs.py`).

## Stage 4: Async Parity

- [x] Core async modules documented (`async_devices`, `async_events`, `async_thresholds`, `async_device_capabilities`, `async_ingestion`, `async_readings`).
- [x] Remaining async modules documented (`async_sensor_types`, `async_capabilities`, `async_capability_groups`, `async_automation`, `async_alerts`, `async_farms`, `async_commands`, `async_client`).
- [x] Part 1 checker passes (`scripts/check_stage4_part1_async_docs.py`).
- [x] Global completeness checker passes for all functions/methods.

## Stage 5: Polish + Quality Gates

- [x] CI docs job runs:
  - `sphinx-build -W --keep-going -b html docs-site docs-site/_build/html`
  - `python scripts/check_docs_completeness.py --package-dir python/vfarm_device_sdk`
  - `sphinx-build -b linkcheck docs-site docs-site/_build/linkcheck` (blocking).
- [x] Contributing guide added: `docs/DOCS_CONTRIBUTING.md`.
- [x] Stage completion checklist added: `docs/SDK_DOCS_STAGE_CHECKLIST.md`.
- [x] Linkcheck promoted to blocking after link cleanup.
