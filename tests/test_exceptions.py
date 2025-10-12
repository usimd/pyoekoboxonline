"""Tests for Ökobox Online API exceptions."""

import httpx

from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxError,
    OekoboxValidationError,
)


class TestExceptions:
    """Test cases for custom exception classes."""

    def test_oekobox_error_base(self):
        """Test base OekoboxError exception."""
        error = OekoboxError("Base error", status_code=500)
        assert str(error) == "Base error"
        assert error.message == "Base error"
        assert error.status_code == 500
        assert isinstance(error, Exception)

    def test_oekobox_api_error(self):
        """Test OekoboxAPIError exception."""
        error = OekoboxAPIError("API request failed", status_code=400)
        assert str(error) == "API request failed"
        assert error.status_code == 400
        assert isinstance(error, OekoboxError)

    def test_oekobox_api_error_with_response_data(self):
        """Test OekoboxAPIError with response data."""
        response_data = {"error": "Invalid request", "code": "INVALID_PARAM"}
        error = OekoboxAPIError(
            "Server error", status_code=400, response_data=response_data
        )
        assert "Server error" in str(error)
        assert error.response_data == response_data
        assert error.status_code == 400

    def test_oekobox_authentication_error(self):
        """Test OekoboxAuthenticationError exception."""
        error = OekoboxAuthenticationError("Invalid credentials", status_code=401)
        assert str(error) == "Invalid credentials"
        assert error.status_code == 401
        assert isinstance(error, OekoboxAPIError)

    def test_oekobox_connection_error(self):
        """Test OekoboxConnectionError exception."""
        original_error = httpx.ConnectError("Network unreachable")
        error = OekoboxConnectionError(
            "Connection timeout", original_error=original_error
        )
        assert str(error) == "Connection timeout"
        assert error.original_error == original_error
        assert isinstance(error, OekoboxError)

    def test_oekobox_validation_error(self):
        """Test OekoboxValidationError exception."""
        error = OekoboxValidationError("Invalid data format")
        assert str(error) == "Invalid data format"
        assert isinstance(error, OekoboxError)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit correctly."""
        auth_error = OekoboxAuthenticationError("Auth failed", status_code=401)
        conn_error = OekoboxConnectionError("Connection failed")
        validation_error = OekoboxValidationError("Validation failed")

        assert isinstance(auth_error, OekoboxAPIError)
        assert isinstance(auth_error, OekoboxError)
        assert isinstance(conn_error, OekoboxError)
        assert isinstance(validation_error, OekoboxError)

    def test_exception_with_original_exception(self):
        """Test exceptions that wrap original exceptions."""
        original_error = httpx.ConnectError("Network unreachable")
        wrapped_error = OekoboxConnectionError(
            "Failed to connect", original_error=original_error
        )

        assert "Failed to connect" in str(wrapped_error)
        assert wrapped_error.original_error == original_error
