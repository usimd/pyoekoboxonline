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
        status_code = 400
        error = OekoboxAPIError(message, status_code)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code
        assert error.response_data == {}

    def test_oekobox_api_error_with_response_data(self):
        """Test OekoboxAPIError with response data."""
        message = "API request failed"
        status_code = 400
        response_data = {"error_code": "INVALID_ITEM", "details": "Item not found"}
        error = OekoboxAPIError(message, status_code, response_data)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code
        assert error.response_data == response_data

    def test_oekobox_authentication_error(self):
        """Test OekoboxAuthenticationError creation."""
        message = "Invalid credentials"
        status_code = 401
        error = OekoboxAuthenticationError(message, status_code)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code

    def test_oekobox_connection_error(self):
        """Test OekoboxConnectionError creation."""
        message = "Connection timeout"
        error = OekoboxConnectionError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None

    def test_oekobox_validation_error(self):
        """Test OekoboxValidationError creation."""
        message = "Invalid data format"
        error = OekoboxValidationError(message)
        assert str(error) == message
        assert error.message == message
        assert error.status_code is None

    def test_exception_chaining(self):
        """Test that exceptions can be chained properly."""
        original_error = ValueError("Original error")

        try:
            raise OekoboxAPIError("API failed", 500) from original_error
        except OekoboxAPIError as e:
            assert e.message == "API failed"
            assert e.status_code == 500
            assert e.__cause__ == original_error

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
        status_code = 500
        error = OekoboxAPIError(message, status_code, None)
        assert error.response_data == {}
