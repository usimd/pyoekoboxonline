"""Exception classes for the Ökobox Online API client."""


class OekoboxError(Exception):
    """Base exception for all Ökobox API related errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OekoboxAPIError(OekoboxError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_data: dict[str, str | int] | None = None,
    ) -> None:
        super().__init__(message, status_code)
        self.response_data = response_data or {}


class OekoboxConnectionError(OekoboxError):
    """Raised when there's a connection error to the API."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class OekoboxAuthenticationError(OekoboxAPIError):
    """Raised when authentication fails."""

    pass


class OekoboxValidationError(OekoboxError):
    """Raised when request validation fails."""

    pass
