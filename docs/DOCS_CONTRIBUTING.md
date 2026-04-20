# How To Contribute SDK Docs

This repo uses Sphinx docs in `docs-site/` and enforces docstring coverage for all functions/methods in `python/vfarm_device_sdk`.

## Local Docs Commands

```bash
pip install -e .[dev]
sphinx-build -W --keep-going -b html docs-site docs-site/_build/html
python scripts/check_docs_completeness.py --package-dir python/vfarm_device_sdk
```

Link check:

```bash
sphinx-build -b linkcheck docs-site docs-site/_build/linkcheck
```

## Required Docstring Sections

Every function/method docstring must include:

- `Parameters`
- `Returns`
- `Examples`
- `Common Errors`

`Common Errors` should map common HTTP/status or runtime failure modes to SDK exceptions and expected cause.

## Reusable Per-Function Snippet

```rst
One-line summary.

Parameters
----------
arg_name:
    What this argument means.

Returns
-------
ReturnType
    What this function returns.

Examples
--------
.. code-block:: python

   value = client.some_method(...)
   print(value)

Common Errors
-------------
- ``400/422`` -> ``ValidationError``: Invalid request data.
- ``401`` -> ``AuthenticationError``: Invalid farm API key.
- ``404`` -> ``NotFoundError``: Resource not found.
- ``5xx`` -> ``VFarmApiError``: Server-side failure.
```

## Authoring Notes

- Keep examples minimal and executable-looking.
- Prefer real SDK types in examples (`DeviceCreate`, `CommandCreate`, etc.).
- For pure helpers with no API call, document runtime/validation errors and use `N/A` status where appropriate.
