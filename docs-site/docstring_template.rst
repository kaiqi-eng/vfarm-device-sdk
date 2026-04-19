Docstring Standard
==================

All functions and methods in ``python/vfarm_device_sdk`` must include a docstring
using this template.

Required sections:

- Summary (single sentence)
- Parameters
- Returns
- Examples
- Common Errors

Template:

.. code-block:: rst

   def function_name(arg1: str, arg2: int = 0) -> ReturnType:
       """
       Short summary of what this function does.

       Parameters
       ----------
       arg1:
           Description of argument.
       arg2:
           Description of argument.

       Returns
       -------
       ReturnType
           Description of the return value.

       Examples
       --------
       .. code-block:: python

          from vfarm_device_sdk import VFarmClient

          with VFarmClient(base_url="http://localhost:8003", api_key="...") as client:
              result = client.function_name(...)
              print(result)

       Common Errors
       -------------
       - ``400`` -> ``ValidationError``: Invalid request payload.
       - ``401`` -> ``AuthenticationError``: Missing/invalid API key.
       - ``404`` -> ``NotFoundError``: Referenced resource not found.
       - ``409`` -> ``ConflictError``: Resource already exists or conflicting state.
       - ``5xx`` -> ``VFarmApiError``: Server-side failure.
       """

Validation:

- ``scripts/check_docs_completeness.py`` enforces:
  - every function/method has a docstring,
  - ``Examples`` section exists,
  - ``Common Errors`` section exists.

