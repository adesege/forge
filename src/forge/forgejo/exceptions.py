"""Forgejo API exceptions."""

from __future__ import annotations


class ForgejoAPIError(Exception):
    """Base exception for Forgejo API errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Forgejo API error {status_code}: {message}")


class ForgejoNotFoundError(ForgejoAPIError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(404, message)


class ForgejoAuthError(ForgejoAPIError):
    """Authentication or authorization error (401/403)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(401, message)


class ForgejoValidationError(ForgejoAPIError):
    """Validation error (422)."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(422, message)
