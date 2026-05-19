from __future__ import annotations

from typing import Any


class TimeTrackError(Exception):
    """Base exception for all application-raised errors.

    Each subclass owns a stable ``code`` (used in the JSON error envelope) and
    a default HTTP ``status``. Endpoints catch ``TimeTrackError`` and serialize.
    """

    code: str = "internal_error"
    status: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_envelope(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(TimeTrackError):
    code = "not_found"
    status = 404


class ValidationError(TimeTrackError):
    code = "validation_error"
    status = 422


class AuthenticationError(TimeTrackError):
    code = "authentication_required"
    status = 401


class ForbiddenError(TimeTrackError):
    code = "forbidden"
    status = 403


class ConflictError(TimeTrackError):
    code = "conflict"
    status = 409
