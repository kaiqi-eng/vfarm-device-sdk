from __future__ import annotations


class VFarmApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, detail: object | None = None):
        """
        Base SDK API exception carrying HTTP status and detail.

        Parameters
        ----------
        message:
            Human-readable error message.
        status_code:
            Optional HTTP status code.
        detail:
            Optional backend error detail payload.

        Returns
        -------
        None
            Initializes exception fields.

        Examples
        --------
        .. code-block:: python

           err = VFarmApiError("Failed", status_code=500, detail={"error": "internal"})
           print(err.status_code)

        Common Errors
        -------------
        - ``N/A`` -> ``None``: Constructor does not perform network operations.
        """
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class AuthenticationError(VFarmApiError):
    pass


class ValidationError(VFarmApiError):
    pass


class NotFoundError(VFarmApiError):
    pass


class ConflictError(VFarmApiError):
    pass
