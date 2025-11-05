"""Tests for the Ökobox Online API client."""

import aiohttp
import pytest
from aioresponses import aioresponses

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
)
from pyoekoboxonline.models import Group, Item, Order, XUnit


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
    async def test_client_initialization_with_external_session(self):
        """Test client initialization with external session."""
        async with aiohttp.ClientSession() as external_session:
            client = OekoboxClient(
                shop_id="test_shop",
                username="testuser",
                password="testpass",
                session=external_session,
            )
            assert client._client is external_session
            assert client._owns_session is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        async with OekoboxClient("test_shop", "user", "pass") as client:
            assert client._client is not None
            assert isinstance(client._client, aiohttp.ClientSession)
            assert client._owns_session is True

    @pytest.mark.asyncio
    async def test_external_session_not_closed(self):
        """Test that external session is not closed by client."""
        async with aiohttp.ClientSession() as external_session:
            client = OekoboxClient(
                "test_shop", "user", "pass", session=external_session
            )
            await client.close()
            assert not external_session.closed

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
    async def test_request_success(self):
        """Test successful HTTP request."""
        with aioresponses() as m:
            m.get("http://example.com/api/test", payload={"result": "ok"})

            async with OekoboxClient("test_shop", "user", "pass") as client:
                response = await client._request("GET", "http://example.com/api/test")
                assert response == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_with_session_id(self):
        """Test request with session ID parameter."""
        with aioresponses() as m:
            m.get(
                "http://example.com/api/test?x-oekobox-sid=test_session_123",
                payload={"result": "ok"},
            )

            async with OekoboxClient("test_shop", "user", "pass") as client:
                client.session_id = "test_session_123"
                response = await client._request("GET", "http://example.com/api/test")
                assert response == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_extracts_session_id_from_cookies(self):
        """Test session ID extraction from response cookies."""
        with aioresponses() as m:
            m.get(
                "http://example.com/api/test",
                payload={"result": "ok"},
                headers={"Set-Cookie": "JSESSIONID=abc123; Path=/"},
            )

            async with OekoboxClient("test_shop", "user", "pass") as client:
                await client._request("GET", "http://example.com/api/test")
                assert client.session_id == "abc123"

    @pytest.mark.asyncio
    async def test_request_http_error_401(self):
        """Test HTTP 401 error handling."""
        with aioresponses() as m:
            m.get("http://example.com/api/test", status=401, body="Unauthorized")

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxAuthenticationError, match="HTTP 401"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_request_http_error_403(self):
        """Test HTTP 403 error handling."""
        with aioresponses() as m:
            m.get("http://example.com/api/test", status=403, body="Forbidden")

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxAuthenticationError, match="HTTP 403"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_request_http_error_404(self):
        """Test HTTP 404 error handling."""
        with aioresponses() as m:
            m.get("http://example.com/api/test", status=404, body="Not Found")

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxAPIError, match="HTTP 404: Not found"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_request_http_error_409(self):
        """Test HTTP 409 error handling."""
        with aioresponses() as m:
            m.get("http://example.com/api/test", status=409, body="Conflict")

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxAPIError, match="HTTP 409: Conflict error"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_request_http_error_500(self):
        """Test HTTP 500 error handling."""
        with aioresponses() as m:
            m.get(
                "http://example.com/api/test",
                status=500,
                payload={"error": "Internal server error"},
            )

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxAPIError, match="HTTP 500"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_request_connection_error(self):
        """Test connection error handling."""
        with aioresponses() as m:
            m.get(
                "http://example.com/api/test",
                exception=aiohttp.ClientConnectionError("Connection failed"),
            )

            async with OekoboxClient("test_shop", "user", "pass") as client:
                with pytest.raises(OekoboxConnectionError, match="Request failed"):
                    await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    async def test_logon_success(self):
        """Test successful logon."""
        with aioresponses() as m:
            # Match URL with query parameters
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/logon2?cid=testuser&pass=testpass",
                payload={
                    "result": "ok",
                    "pcgifversion": "1.0",
                    "shopversion": "2.1",
                },
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                response = await client.logon()
                assert response["result"] == "ok"
                assert response["pcgifversion"] == "1.0"
                assert response["shopversion"] == "2.1"

    @pytest.mark.asyncio
    async def test_logon_failure(self):
        """Test logon failure."""
        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/logon2?cid=testuser&pass=wrongpass",
                payload={"result": "wrong_password"},
            )

            async with OekoboxClient("test_shop", "testuser", "wrongpass") as client:
                with pytest.raises(
                    OekoboxAuthenticationError,
                    match="Wrong password",
                ):
                    await client.logon()

    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout method."""
        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/logout?x-oekobox-sid=test_session",
                payload={"result": "ok"},
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                client.session_id = "test_session"
                response = await client.logout()
                assert response["result"] == "ok"
                assert client.session_id is None

    @pytest.mark.asyncio
    async def test_get_groups(self):
        """Test getting product groups."""
        mock_response = [
            {
                "type": "Group",
                "data": [
                    [1, "Fruits", "Fresh fruits", 25, 5, "bio,organic", 1, 1],
                    [2, "Vegetables", "Fresh vegetables", 30, 8, "regional", 0, 1],
                    [0],  # Terminating entry
                ],
            }
        ]

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/groups4",
                payload=mock_response,
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                groups = await client.get_groups()
                assert len(groups) == 2
                assert isinstance(groups[0], Group)
                assert groups[0].id == 1
                assert groups[0].name == "Fruits"
                assert groups[0].infotext == "Fresh fruits"
                assert groups[0].count == 25

    @pytest.mark.asyncio
    async def test_get_items(self):
        """Test getting items."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Apple", 2.50, "kg", "Fresh red apples", 1, 7.0],
                    [2, "Banana", 1.80, "kg", "Yellow bananas", 1, 7.0],
                    [0],  # Terminating entry
                ],
            }
        ]

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/items",
                payload=mock_response,
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                items = await client.get_items()
                assert len(items) == 2
                assert isinstance(items[0], Item)
                assert items[0].id == 1
                assert items[0].name == "Apple"
                assert items[0].price == 2.50
                assert items[0].unit == "kg"

    @pytest.mark.asyncio
    async def test_get_item(self):
        """Test getting a specific item."""
        # get_item expects a raw list response (not wrapped in DataList format)
        mock_response = [1, "Apple", 2.50, "kg", "Fresh red apples", 1, 7.0]

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/item/1",
                payload=mock_response,
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                item = await client.get_item(1)
                assert isinstance(item, Item)
                assert item.id == 1
                assert item.name == "Apple"
                assert item.price == 2.50
                assert item.unit == "kg"

    @pytest.mark.asyncio
    async def test_get_itemlist(self):
        """Test getting item list."""
        import re

        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Apple", 2.50, "kg", "Fresh red apples", 1, 7.0],
                    [2, "Banana", 1.80, "kg", "Yellow bananas", 1, 7.0],
                    [0],
                ],
            },
            {
                "type": "XUnit",
                "data": [
                    [1, "piece", "1", "S", 1, "1"],
                    [2, "piece", "1", "S", 2, "1"],
                    [0],
                ],
            },
        ]

        with aioresponses() as m:
            # Use regex to match the URL with encoded parameters
            m.get(
                re.compile(
                    r"https://oekobox-online\.de/v3/shop/test_shop/api/itemlist16\?i=.*"
                ),
                payload=mock_response,
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                result = await client.get_itemlist([1, 2])
                # Should return mixed types: Items and XUnits
                items = [r for r in result if isinstance(r, Item)]
                xunits = [r for r in result if isinstance(r, XUnit)]
                assert len(items) == 2
                assert len(xunits) == 2

    @pytest.mark.asyncio
    async def test_get_orders(self):
        """Test getting orders."""
        mock_response = [
            {
                "type": "Order",
                "data": [
                    [1, "2024-01-15", "0", 1, "Customer note", "Delivery note"],
                    [2, "2024-01-16", "1", 2, "", "Handle with care"],
                    [0],
                ],
            }
        ]

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/shop/test_shop/api/orders",
                payload=mock_response,
            )

            async with OekoboxClient("test_shop", "testuser", "testpass") as client:
                orders = await client.get_orders()
                assert len(orders) == 2
                assert isinstance(orders[0], Order)
                assert orders[0].id == 1
                assert orders[0].ddate == "2024-01-15"
