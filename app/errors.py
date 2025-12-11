from typing import Any, Optional


class AppError(Exception):
    """Base application error that carries an HTTP status and machine code.

    Attributes:
        status_code: HTTP status code to return
        code: short machine-readable error code
        message: human-readable message
        details: optional structured details
    """

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class BadRequest(AppError):
    status_code = 400
    code = "bad_request"


class NotFound(AppError):
    status_code = 404
    code = "not_found"


class Unauthorized(AppError):
    status_code = 401
    code = "unauthorized"


class Forbidden(AppError):
    status_code = 403
    code = "forbidden"


class Conflict(AppError):
    status_code = 409
    code = "conflict"


class InternalError(AppError):
    status_code = 500
    code = "internal_error"
