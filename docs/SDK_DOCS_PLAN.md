# Sphinx SDK Docs Rollout (Staged, Exhaustive Function Coverage)

## Summary

Build a dedicated Sphinx site in `docs-site/` that documents every function/method in `python/vfarm_device_sdk` (including internal/private helpers), with:

- per-function usage example (from docstrings),
- exhaustive common errors/error-code matrix (derived from OpenAPI + SDK exception mapping),
- staged delivery to keep each implementation chunk small.

Chosen defaults:

- Sphinx stack
- docstring-based examples
- sync-first, async-second execution order
- exhaustive endpoint error matrix
- include absolutely every function
- dedicated `docs-site/` directory

## Implementation Changes (By Stage)

### Stage 1: Sphinx foundation + docs contract enforcement

- Add `docs-site/` with `conf.py`, `index.rst`, API toctree layout, and build Makefile helpers.
- Enable extensions: `autodoc`, `autosummary`, `napoleon`, `viewcode`, `myst_parser`, `intersphinx`.
- Add docs dependencies to dev extras (Sphinx + selected extensions).
- Add a verification script (`scripts/check_docs_completeness.py`) that fails if any package function/method is missing docs/example/errors sections.
- Define standard docstring template for all functions:
  - one-line summary
  - args/returns
  - `Examples` block
  - `Common Errors` block (status code -> SDK exception -> cause/handling)

### Stage 2: Sync surface documentation (first half)

- Document sync core + primary operational modules first: `core`, `devices`, `events`, `thresholds`, `device_capabilities`, `ingestion`, `readings`.
- Add/normalize docstrings for all functions in these modules, including private/internal functions.
- Generate autosummary pages and ensure each function page renders signature + example + error section.
- Build first pass of endpoint-to-error mapping from `_request()` call literals and OpenAPI responses.

### Stage 3: Remaining sync modules + exhaustive error matrix completion

- Document remaining sync modules: `commands`, `farms`, `sensor_types`, `capabilities`, `capability_groups`, `automation`, `alerts`, `idempotency`, `exceptions`, `client`.
- Complete exhaustive error matrix logic:
  - for endpoint-backed functions: OpenAPI response codes + SDK exception mapping in `core.py`;
  - for orchestration methods (for example `ensure_*`): include multi-call flow errors;
  - for non-endpoint helpers: document runtime/validation exceptions explicitly.
- Add dedicated "Error Codes Reference" pages grouped by endpoint and function.

### Stage 4: Async parity pass

- Document all async modules with mirrored structure and async-specific examples:
  `async_*` modules + `async_client`.
- Ensure every async function has example + exhaustive errors section aligned with sync counterpart behavior.
- Add cross-links between sync and async variants on each function page.

### Stage 5: Polish, quality gates, and CI integration

- Add CI docs job:
  - `sphinx-build -W --keep-going`
  - docs completeness checker
  - optional `linkcheck` (non-blocking initially, then blocking after cleanup).
- Add "How to contribute docs" guide and a reusable per-function docstring snippet.
- Add stage-completion checklist with objective acceptance criteria per module group.

## Public Interfaces / Types Changes

- No runtime API behavior changes planned.
- Developer-facing additions:
  - new docs build commands (for example `make -C docs-site html`),
  - new docs quality-check command/script,
  - expanded function docstrings across SDK modules.

## Test Plan

- `sphinx-build` succeeds with warnings treated as errors.
- Completeness checker confirms:
  - 100% function/method coverage in `python/vfarm_device_sdk`,
  - every function has `Examples` and `Common Errors` sections.
- Spot validation on representative functions:
  - simple endpoint wrapper (`get_device`)
  - helper/orchestration (`ensure_device`)
  - internal helper (`_request` / payload merge helper)
  - async parity method (`async get_device`).
- Regression check: existing unit tests still pass (no behavioral changes expected).

## Assumptions

- Source of truth for endpoint error codes is `contracts/openapi_source.json` (and related contract files already in repo).
- Existing markdown docs under `docs/` remain as narrative references; canonical generated API site lives in `docs-site/`.
- "Comprehensive" means all package functions/methods, including private/internal ones, not only exported client methods.
