"""Tests for Ökobox Online API exceptions."""

from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxError,
    OekoboxValidationError,
)


class TestOekoboxExceptions:
    """Test cases for Ökobox Online API exception classes."""

    def test_oekobox_error_base_exception(self):
        """Test base OekoboxError exception."""
        message = "Base error message"
        error = OekoboxError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None

    def test_oekobox_error_with_status_code(self):
        """Test base OekoboxError exception with status code."""
        message = "Base error message"
        status_code = 500
        error = OekoboxError(message, status_code=status_code)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code

    def test_oekobox_error_inheritance(self):
        """Test that all exceptions inherit from OekoboxError."""
        assert issubclass(OekoboxAPIError, OekoboxError)
        assert issubclass(OekoboxAuthenticationError, OekoboxError)
        assert issubclass(OekoboxConnectionError, OekoboxError)
        assert issubclass(OekoboxValidationError, OekoboxError)

    def test_oekobox_api_error_basic(self):
        """Test basic OekoboxAPIError creation."""
        message = "API request failed"
        error_message = "err"
        status_code = 400
        error = OekoboxAPIError(message, error_message, status_code)
        assert str(error) == message
        assert error.message == message
        assert error.internal_error == error_message
        assert error.status_code == status_code
        assert error.response_data == {}

    def test_oekobox_api_error_with_response_data(self):
        """Test OekoboxAPIError with response data."""
        message = "API request failed"
        error_message = "err"
        status_code = 400
        response_data = {"error": "Bad request", "details": "Invalid parameters"}
        error = OekoboxAPIError(message, error_message, status_code, response_data)
        assert str(error) == message
        assert error.message == message
        assert error.internal_error == error_message
        assert error.status_code == status_code
        assert error.response_data == response_data

    def test_oekobox_authentication_error(self):
        """Test OekoboxAuthenticationError."""
        message = "Authentication failed"
        error_message = "err"
        status_code = 401
        error = OekoboxAuthenticationError(message, error_message, status_code)
        assert str(error) == message
        assert error.message == message
        assert error.internal_error == error_message
        assert error.status_code == status_code
        assert isinstance(error, OekoboxError)

    def test_oekobox_connection_error(self):
        """Test OekoboxConnectionError."""
        message = "Connection refused"
        error = OekoboxConnectionError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None
        assert isinstance(error, OekoboxError)

    def test_oekobox_validation_error(self):
        """Test OekoboxValidationError."""
        message = "Validation failed"
        error = OekoboxValidationError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None
        assert isinstance(error, OekoboxError)

    def test_exception_chain_preservation(self):
        """Test that exception chaining is preserved."""
        original_error = ValueError("Original error")
        error_message = "err"
        wrapped_error = OekoboxAPIError("Wrapped error", error_message, 500)
        wrapped_error.__cause__ = original_error

        assert wrapped_error.__cause__ == original_error
        assert str(wrapped_error) == "Wrapped error"

    def test_authentication_error_without_status_code(self):
        """Test authentication error without status code."""
        message = "Authentication failed"
        error = OekoboxAuthenticationError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None

    def test_api_error_with_none_response_data(self):
        """Test API error with None response data."""
        message = "API error"
        error_message = "err"
        status_code = 500
        error = OekoboxAPIError(message, error_message, status_code, None)
        assert error.response_data == {}
