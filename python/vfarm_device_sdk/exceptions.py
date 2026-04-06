from __future__ import annotations


class VFarmApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, detail: object | None = None):
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
