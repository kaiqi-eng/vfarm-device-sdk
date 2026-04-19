Function Error Matrix
=====================

This page groups common errors by function family for Stage 3 sync modules.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Module
     - Function families
     - Common errors
   * - ``commands.py``
     - ``fetch/list/create/update/cancel`` and ``enqueue_*`` helpers
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create/update paths), ``5xx VFarmApiError``
   * - ``farms.py``
     - ``list/get/create/update/delete/reactivate/deactivate/ensure/iter``
     - ``400/422 ValidationError`` (list/create/update), ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``sensor_types.py``
     - ``list/get/create/update/delete/remove_capability/ensure``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``capabilities.py``
     - ``list/get/create/update/delete/ensure/iter``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``capability_groups.py``
     - ``list/get/create/update/delete/add/remove/ensure/iter``
     - ``400/422 ValidationError`` (create/update/add), ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create/add), ``5xx VFarmApiError``
   * - ``automation.py``
     - ``list/get/create/update/delete/enable/disable/stats/history/iter_*``
     - ``400/422 ValidationError`` (query/write paths), ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``alerts.py``
     - channels, rules, history, ``test_alert_channel`` and iterators
     - ``400/422 ValidationError`` (query/write paths), ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``idempotency.py``
     - ``generate_idempotency_key``, ``with_idempotency_header``, ``_normalize_prefix``
     - No HTTP exceptions (pure helpers)
   * - ``exceptions.py``
     - ``VFarmApiError.__init__``
     - No HTTP exceptions (constructor only)
   * - ``client.py``
     - ``VFarmClient`` facade composition
     - Inherits all mixin exceptions listed above

