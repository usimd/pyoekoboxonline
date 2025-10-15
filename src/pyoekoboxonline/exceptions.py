"""Custom exceptions for the Ökobox Online API client."""

from typing import Any


class OekoboxError(Exception):
    """Base exception for all Ökobox Online API errors."""

    def __init__(
        self,
        message: str,
        internal_error: str | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize the base exception.

        Args:
            message: Error message
            internal_error: Internal error message returned by the API in the "X-oekobox-error" header
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.message = message
        self.internal_error = internal_error
        self.status_code = status_code


class OekoboxAPIError(OekoboxError):
    """Exception raised for API-level errors."""

    def __init__(
        self,
        message: str,
        internal_error: str | None = None,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Error message
            internal_error: Internal error message returned by the API
            status_code: HTTP status code
            response_data: Raw response data from API
        """
        super().__init__(message, internal_error, status_code)
        self.response_data = response_data or {}


class OekoboxAuthenticationError(OekoboxError):
    """Exception raised for authentication failures."""

    def __init__(
        self,
        message: str,
        internal_error: str | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Error message
            internal_error: Internal error message returned by the API
            status_code: HTTP status code
        """
        super().__init__(message, internal_error, status_code)


class OekoboxConnectionError(OekoboxError):
    """Exception raised for connection and network errors."""

    def __init__(self, message: str) -> None:
        """Initialize connection error.

        Args:
            message: Error message
        """
        super().__init__(message)


class OekoboxValidationError(OekoboxError):
    """Exception raised for data validation errors."""

    def __init__(self, message: str) -> None:
        """Initialize validation error.

        Args:
            message: Error message
        """
        super().__init__(message)
