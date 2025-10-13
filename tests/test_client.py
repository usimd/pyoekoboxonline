"""Tests for the Ökobox Online API client."""

import httpx
import pytest
import respx

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
)
from pyoekoboxonline.models import (
    CustomerInfo,
    UserInfo,
)


class TestOekoboxClient:
    """Test cases for OekoboxClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        assert client.shop_id == "test_shop"
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.base_url == "https://oekobox-online.de/v3/shop/test_shop"
        assert client.timeout == 30.0
        assert client.api_base_url == "https://oekobox-online.de/v3/shop/test_shop/api"

    def test_client_initialization_with_custom_url(self):
        """Test client initialization with custom base URL."""
        client = OekoboxClient(
            shop_id="test_shop",
            username="testuser",
            password="testpass",
            base_url="https://custom.domain.com/shop/test_shop",
            timeout=60.0,
        )
        assert client.base_url == "https://custom.domain.com/shop/test_shop"
        assert client.timeout == 60.0
        assert client.api_base_url == "https://custom.domain.com/shop/test_shop/api"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        async with OekoboxClient("test_shop", "user", "pass") as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test client close method."""
        client = OekoboxClient("test_shop", "user", "pass")
        async with client:
            pass
        # Client should be closed after context manager exit
        await client.close()  # Should not raise an error

    @pytest.mark.asyncio
    async def test_request_without_client_raises_error(self):
        """Test that making requests without initialized client raises error."""
        client = OekoboxClient("test_shop", "user", "pass")
        with pytest.raises(OekoboxConnectionError, match="Client not initialized"):
            await client._request("GET", "http://example.com")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_success(self):
        """Test successful HTTP request."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            response = await client._request("GET", "http://example.com/api/test")
            assert response == {"result": "ok"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_with_session_id(self):
        """Test request with session ID parameter."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            client.session_id = "test_session_123"
            await client._request("GET", "http://example.com/api/test")

            # Check that session ID was added as parameter
            request = respx.calls.last.request
            assert "x-oekobox-sid=test_session_123" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_extracts_session_id_from_cookies(self):
        """Test session ID extraction from response cookies."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(
                200,
                json={"result": "ok"},
                headers={"Set-Cookie": "JSESSIONID=abc123; Path=/"},
            )
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            await client._request("GET", "http://example.com/api/test")
            assert client.session_id == "abc123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_http_error_401(self):
        """Test HTTP 401 error handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxAuthenticationError, match="HTTP 401"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_http_error_403(self):
        """Test HTTP 403 error handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(403, text="Forbidden")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxAuthenticationError, match="HTTP 403"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_http_error_500(self):
        """Test HTTP 500 error handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxAPIError, match="HTTP 500"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_connection_error(self):
        """Test connection error handling."""
        respx.get("http://example.com/api/test").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxConnectionError, match="Connection error"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_api_error_result(self):
        """Test API-level error result handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(200, json={"result": "no_such_user"})
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(
                OekoboxAuthenticationError, match="Authentication failed: no_such_user"
            ):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_available_shops(self):
        """Test getting available shops."""
        mock_response = """[52.520008,13.404954,"Organic Market Berlin",52.530008,13.414954,"berlin_market"]
[48.137154,11.576124,"Munich Organic",48.147154,11.586124,"munich_organic"]"""

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, text=mock_response)
        )

        shops = await OekoboxClient.get_available_shops()
        assert len(shops) == 2
        assert shops[0].id == "berlin_market"
        assert shops[0].name == "Organic Market Berlin"
        assert shops[0].latitude == 52.520008
        assert shops[0].longitude == 13.404954
        assert shops[0].delivery_lat == 52.530008
        assert shops[0].delivery_lng == 13.414954

    @pytest.mark.asyncio
    @respx.mock
    async def test_logon_success(self):
        """Test successful logon."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logon").mock(
            return_value=httpx.Response(
                200,
                json={
                    "action": "Logon",
                    "result": "ok",
                    "pcgifversion": "1.0",
                    "shopversion": "2.1",
                },
            )
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.logon()
            assert isinstance(user_info, UserInfo)
            assert user_info.username == "testuser"
            assert user_info.pcgif_version == "1.0"
            assert user_info.shop_version == "2.1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_logon_failure(self):
        """Test logon failure."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logon").mock(
            return_value=httpx.Response(
                200, json={"action": "Logon", "result": "wrong_password"}
            )
        )

        async with OekoboxClient("test_shop", "testuser", "wrongpass") as client:
            with pytest.raises(
                OekoboxAuthenticationError,
                match="Authentication failed: wrong_password",
            ):
                await client.logon()

    @pytest.mark.asyncio
    @respx.mock
    async def test_logout(self):
        """Test logout method."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logout").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            client.session_id = "test_session"
            await client.logout()
            assert client.session_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_groups(self):
        """Test getting product groups."""
        mock_response = [
            {
                "type": "Group",
                "data": [
                    [1, "Fruits", "Fresh fruits", 25],
                    [2, "Vegetables", "Fresh vegetables", 30],
                    [0],  # Terminating entry
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups2").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            groups = await client.get_groups()
            assert len(groups) == 2
            assert groups[0].id == "1"
            assert groups[0].name == "Fruits"
            assert groups[0].info == "Fresh fruits"
            assert groups[0].count == 25

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_subgroups(self):
        """Test getting product subgroups."""
        mock_response = [
            {"type": "Group", "data": []},
            {
                "type": "SubGroup",
                "data": [
                    [1, "Apples", "1", 5],
                    [2, "Bananas", "1", 3],
                    [0],  # Terminating entry
                ],
            },
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups2").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            subgroups = await client.get_subgroups()
            assert len(subgroups) == 2
            assert subgroups[0].id == "1"
            assert subgroups[0].name == "Apples"
            assert subgroups[0].parent_id == "1"
            assert subgroups[0].count == 5

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_success(self):
        """Test successful get_user_info with complete API response."""
        # Mock response based on scraped API documentation
        mock_response = [
            {
                "type": "UserInfo",
                "version": 4,
                "data": [
                    [
                        "AUTH",
                        12345,
                        "Herr",
                        "Max",
                        "Mustermann",
                        0,
                        1,
                        0,
                        0,
                        0,
                        0,
                        0,
                        1,
                        "max.mustermann@email.com",
                        "backup@email.com",
                        "+49301234567",
                        "+491701234567",
                        "DE",
                        "10115",
                        "Berlin",
                        "Under den Linden 1",
                    ],
                    [0],  # Version info
                ],
            },
            {"type": "SomeOtherType", "data": [["other", "data"]]},
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.get_user_info()

            assert isinstance(user_info, UserInfo)
            assert user_info.authentication_state == "AUTH"
            assert user_info.id == "12345"
            assert user_info.opener == "Herr"
            assert user_info.first_name == "Max"
            assert user_info.last_name == "Mustermann"
            assert user_info.role == 0
            assert user_info.debug_level == 1
            assert user_info.email == "max.mustermann@email.com"
            assert user_info.email1 == "backup@email.com"
            assert user_info.phone == "+49301234567"
            assert user_info.phone1 == "+491701234567"
            assert user_info.country == "DE"
            assert user_info.zip == "10115"
            assert user_info.city == "Berlin"
            assert user_info.street == "Under den Linden 1"
            assert (
                user_info.username == "max.mustermann@email.com"
            )  # Derived from email
            assert user_info.is_active is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_minimal_response(self):
        """Test get_user_info with minimal API response."""
        mock_response = [
            {
                "type": "UserInfo",
                "version": 4,
                "data": [
                    ["VALID", 42],  # Just auth state and ID
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.get_user_info()

            assert user_info.authentication_state == "VALID"
            assert user_info.id == "42"
            assert user_info.username == "42"  # Derived from ID
            assert user_info.is_active is True
            assert user_info.email is None
            assert user_info.first_name is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_single_object_response(self):
        """Test get_user_info with single UserInfo object response format."""
        mock_response = {
            "type": "UserInfo",
            "version": 4,
            "data": [
                [
                    "AUTH",
                    999,
                    "Dr.",
                    "Jane",
                    "Smith",
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    "jane.smith@example.com",
                    "",
                    "+49123456789",
                    "",
                    "DE",
                    "12345",
                    "Munich",
                    "Hauptstraße 10",
                ],
                [0],
            ],
        }

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.get_user_info()

            assert user_info.authentication_state == "AUTH"
            assert user_info.id == "999"
            assert user_info.opener == "Dr."
            assert user_info.first_name == "Jane"
            assert user_info.last_name == "Smith"
            assert user_info.role == 1  # Web-Admin
            assert user_info.email == "jane.smith@example.com"
            assert user_info.phone == "+49123456789"
            assert user_info.country == "DE"
            assert user_info.city == "Munich"
            assert user_info.street == "Hauptstraße 10"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_no_userinfo_in_response(self):
        """Test get_user_info fallback when no UserInfo found in response."""
        mock_response = [{"type": "SomeOtherType", "data": [["other", "data"]]}]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient(
            "test_shop", "testuser@example.com", "testpass"
        ) as client:
            user_info = await client.get_user_info()

            # Should return fallback UserInfo
            assert user_info.username == "testuser@example.com"
            assert user_info.email == "testuser@example.com"
            assert user_info.is_active is True
            assert user_info.authentication_state is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_authentication_states(self):
        """Test different authentication states in get_user_info."""
        test_cases = [
            ("NONE", False),
            ("INVALID", False),
            ("VALID", True),
            ("AUTH", True),
            ("SUPER", True),
            ("ADMIN", True),
        ]

        for auth_state, expected_active in test_cases:
            mock_response = [
                {
                    "type": "UserInfo",
                    "data": [[auth_state, 123, "Test", "User", "Name"]],
                }
            ]

            respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                user_info = await client.get_user_info()
                assert user_info.authentication_state == auth_state
                assert user_info.is_active == expected_active

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_validation_error(self):
        """Test get_user_info handles validation errors properly."""
        # Mock response with invalid JSON - this will be handled gracefully by _request
        mock_response = "invalid json"

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(
                200, text=mock_response, headers={"content-type": "text/plain"}
            )
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            # The method should return a fallback UserInfo when it can't parse the response
            user_info = await client.get_user_info()

            # Should return fallback UserInfo with basic credentials
            assert isinstance(user_info, UserInfo)
            assert user_info.username == "testuser"
            assert user_info.is_active is True
            assert user_info.authentication_state is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_customer_info(self):
        """Test get_customer_info method."""
        async with OekoboxClient(
            "test_shop", "testuser@example.com", "testpass"
        ) as client:
            customer_info = await client.get_customer_info()

            assert isinstance(customer_info, CustomerInfo)
            assert customer_info.id == "testuser@example.com"
            assert customer_info.user_info.username == "testuser@example.com"
            assert customer_info.user_info.email == "testuser@example.com"
            assert customer_info.address is None
