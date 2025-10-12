"""Tests for Ökobox Online API exceptions."""

import httpx

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
        message = "Server error"
        status_code = 500
        response_data = {
            "error": "Internal server error",
            "details": "Database connection failed",
        }
        error = OekoboxAPIError(message, status_code, response_data=response_data)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code
        assert error.response_data == response_data

    def test_oekobox_authentication_error_basic(self):
        """Test basic OekoboxAuthenticationError creation."""
        message = "Invalid credentials"
        status_code = 401
        error = OekoboxAuthenticationError(message, status_code)
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code
        assert error.response_data == {}

    def test_oekobox_authentication_error_with_response_data(self):
        """Test OekoboxAuthenticationError with response data."""
        message = "Authentication failed"
        status_code = 401
        response_data = {"error": "Invalid token"}
        error = OekoboxAuthenticationError(
            message, status_code, response_data=response_data
        )
        assert str(error) == message
        assert error.message == message
        assert error.status_code == status_code
        assert error.response_data == response_data

    def test_oekobox_authentication_error_inheritance(self):
        """Test that OekoboxAuthenticationError inherits from OekoboxAPIError."""
        assert issubclass(OekoboxAuthenticationError, OekoboxAPIError)
        error = OekoboxAuthenticationError("Auth failed", 401)
        assert isinstance(error, OekoboxAPIError)
        assert isinstance(error, OekoboxError)

    def test_oekobox_connection_error_basic(self):
        """Test basic OekoboxConnectionError creation."""
        message = "Connection failed"
        error = OekoboxConnectionError(message)
        assert str(error) == message
        assert error.message == message
        assert error.original_error is None

    def test_oekobox_connection_error_with_original_error(self):
        """Test OekoboxConnectionError with original error."""
        message = "Network timeout"
        original_error = httpx.ConnectTimeout("Connection timed out")
        error = OekoboxConnectionError(message, original_error=original_error)
        assert str(error) == message
        assert error.message == message
        assert error.original_error == original_error

    def test_oekobox_connection_error_with_httpx_error(self):
        """Test OekoboxConnectionError with various httpx errors."""
        # Test with ConnectError
        original_error = httpx.ConnectError("Failed to connect")
        error = OekoboxConnectionError(
            "Connection failed", original_error=original_error
        )
        assert error.original_error == original_error

        # Test with TimeoutException
        original_error = httpx.TimeoutException("Request timed out")
        error = OekoboxConnectionError(
            "Timeout occurred", original_error=original_error
        )
        assert error.original_error == original_error

    def test_oekobox_validation_error_basic(self):
        """Test basic OekoboxValidationError creation."""
        message = "Invalid data format"
        error = OekoboxValidationError(message)
        assert str(error) == message
        assert error.message == message

    def test_oekobox_validation_error_with_pydantic_error(self):
        """Test OekoboxValidationError with Pydantic validation error."""
        from pydantic import BaseModel, Field, ValidationError

        class TestModel(BaseModel):
            email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
            age: int = Field(..., gt=0)

        try:
            TestModel(email="invalid-email", age=-5)
        except ValidationError:
            message = "Model validation failed"
            error = OekoboxValidationError(message)
            assert str(error) == message
            assert error.message == message
            # Note: Current implementation doesn't store validation_errors
            # This test verifies the exception can be created successfully

    def test_exception_chaining(self):
        """Test that exceptions can be properly chained."""
        try:
            raise httpx.ConnectError("Original network error")
        except httpx.ConnectError as original:
            connection_error = OekoboxConnectionError(
                "Failed to connect to API", original_error=original
            )
            assert connection_error.original_error == original
            assert str(connection_error.original_error) == "Original network error"

    def test_exception_equality(self):
        """Test exception equality comparison."""
        error1 = OekoboxAPIError("Test error", 400)
        error2 = OekoboxAPIError("Test error", 400)
        error3 = OekoboxAPIError("Different error", 400)
        error4 = OekoboxAPIError("Test error", 500)

        # Same message and status code should be equal
        assert error1.message == error2.message
        assert error1.status_code == error2.status_code

        # Different messages should not be equal
        assert error1.message != error3.message

        # Different status codes should not be equal
        assert error1.status_code != error4.status_code

    def test_exception_representation(self):
        """Test string representation of exceptions."""
        # Test basic error
        error = OekoboxError("Basic error")
        assert str(error) == "Basic error"

        # Test API error with status code
        api_error = OekoboxAPIError("API error", 404)
        assert str(api_error) == "API error"
        assert api_error.status_code == 404

        # Test authentication error
        auth_error = OekoboxAuthenticationError("Auth failed", 401)
        assert str(auth_error) == "Auth failed"
        assert auth_error.status_code == 401

        # Test connection error with original
        original = Exception("Original error")
        conn_error = OekoboxConnectionError(
            "Connection failed", original_error=original
        )
        assert str(conn_error) == "Connection failed"
        assert conn_error.original_error == original

        # Test validation error
        validation_error = OekoboxValidationError("Validation failed")
        assert str(validation_error) == "Validation failed"

    def test_exception_attributes_defaults(self):
        """Test that exception attributes have proper defaults."""
        # Base error
        error = OekoboxError("Test")
        assert hasattr(error, "message")
        assert error.message == "Test"
        assert error.status_code is None

        # API error
        api_error = OekoboxAPIError("Test", 400)
        assert api_error.status_code == 400
        assert api_error.response_data == {}

        # Connection error
        conn_error = OekoboxConnectionError("Test")
        assert conn_error.original_error is None

        # Validation error
        val_error = OekoboxValidationError("Test")
        assert val_error.message == "Test"
