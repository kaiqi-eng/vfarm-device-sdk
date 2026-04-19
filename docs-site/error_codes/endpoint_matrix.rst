Endpoint Error Matrix
=====================

The SDK maps backend HTTP responses to exception types in ``vfarm_device_sdk.core``:

- ``401`` -> ``AuthenticationError``
- ``404`` -> ``NotFoundError``
- ``409`` -> ``ConflictError``
- ``400``/``422`` -> ``ValidationError``
- any other non-2xx -> ``VFarmApiError``
- network/timeout transport failures -> ``VFarmApiError``

Sync endpoint matrix (used by sync mixins):

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Endpoint family
     - Typical methods
     - Common errors
   * - ``/api/v1/devices`` + subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError``, ``5xx VFarmApiError``
   * - ``/api/v1/devices/{id}/events``
     - ``GET``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``5xx VFarmApiError``
   * - ``/api/v1/devices/{id}/thresholds`` + metric subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/devices/{id}/capabilities`` + capability subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/ingest``
     - ``POST``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError`` (linked resources), ``5xx VFarmApiError``
   * - ``/api/v1/readings`` + ``latest`` + ``stats``
     - ``GET``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``5xx VFarmApiError``
   * - ``/api/v1/health``
     - ``GET``
     - ``401 AuthenticationError``, ``5xx VFarmApiError``
   * - ``/api/v1/farms`` + farm subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/sensor-types`` + subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/capabilities`` + capability subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/capability-groups`` + membership subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create/membership), ``5xx VFarmApiError``
   * - ``/api/v1/automation/rules`` + ``stats`` + ``history``
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/alerts/channels`` + ``test``
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/alerts/rules`` + ``history``
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (create), ``5xx VFarmApiError``
   * - ``/api/v1/devices/{id}/commands`` + command subpaths
     - ``GET/POST/PATCH/DELETE``
     - ``400/422 ValidationError``, ``401 AuthenticationError``, ``404 NotFoundError``, ``409 ConflictError`` (state conflict), ``5xx VFarmApiError``

