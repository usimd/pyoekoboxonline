"""Tests for the Ökobox Online API client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.exceptions import (
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxValidationError,
)
from pyoekoboxonline.models import Group, Item, Shop, UserInfo


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
        assert client.base_url == "https://test_shop.oekobox-online.de"

    def test_client_initialization_with_custom_url(self):
        """Test client initialization with custom base URL."""
        client = OekoboxClient(
            shop_id="test_shop",
            username="testuser",
            password="testpass",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        with (
            patch.object(
                OekoboxClient, "logout", new_callable=AsyncMock
            ) as mock_logout,
            patch.object(OekoboxClient, "close", new_callable=AsyncMock) as mock_close,
        ):
            async with OekoboxClient(
                shop_id="test_shop", username="testuser", password="testpass"
            ) as client:
                assert client.shop_id == "test_shop"

            mock_logout.assert_called_once()
            mock_close.assert_called_once()

    def test_build_url(self):
        """Test URL building helper method."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        url = client._build_url("/json/items")
        assert url == "https://test_shop.oekobox-online.de/json/items"

        url = client._build_url("json/user")  # Test without leading slash
        assert url == "https://test_shop.oekobox-online.de/json/user"

    @pytest.mark.asyncio
    async def test_client_close(self):
        """Test proper client cleanup."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        # Mock the httpx client
        with patch.object(
            client._client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    @respx.mock
    async def test_login_success(self):
        """Test successful login."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_response = {
            "id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
            "sessionid": "session_abc123",
        }

        respx.post("https://test_shop.oekobox-online.de/json/logon").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        user_info = await client.login()
        assert isinstance(user_info, UserInfo)
        assert user_info.username == "testuser"
        assert client.session_id == "session_abc123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_groups_success(self):
        """Test successful groups retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_groups = [
            {"id": "fruits", "name": "Fresh Fruits"},
            {"id": "vegetables", "name": "Vegetables"},
        ]

        respx.get("https://test_shop.oekobox-online.de/json/groups").mock(
            return_value=httpx.Response(200, json=mock_groups)
        )

        groups = await client.get_groups()
        assert len(groups) == 2
        assert isinstance(groups[0], Group)
        assert groups[0].id == "fruits"
        assert groups[1].name == "Vegetables"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_items_success(self):
        """Test successful items retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_items = [
            {
                "id": "item_1",
                "name": "Organic Apples",
                "price": 3.99,
                "is_available": True,
            }
        ]

        respx.get("https://test_shop.oekobox-online.de/json/items").mock(
            return_value=httpx.Response(200, json=mock_items)
        )

        items = await client.get_items()
        assert len(items) == 1
        assert isinstance(items[0], Item)
        assert items[0].name == "Organic Apples"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_available_shops_success(self):
        """Test successful available shops retrieval."""
        # Mock the shop list response in JavaScript array format
        mock_js_content = """
        [52.5200,13.4050,"Berlin Organic Market",52.5300,13.4150,"berlin_shop"]
        [48.1351,11.5820,"Munich Bio Store",48.1400,11.5900,"munich_shop"]
        """

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, content=mock_js_content)
        )

        shops = await OekoboxClient.get_available_shops()
        assert len(shops) == 2
        assert isinstance(shops[0], Shop)
        assert shops[0].id == "berlin_shop"
        assert shops[0].name == "Berlin Organic Market"

    @pytest.mark.asyncio
    @respx.mock
    async def test_connection_error(self):
        """Test connection error handling."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        respx.post("https://test_shop.oekobox-online.de/json/logon").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(OekoboxConnectionError):
            await client.login()

    @pytest.mark.asyncio
    @respx.mock
    async def test_authentication_error(self):
        """Test authentication error handling."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="wrongpass"
        )

        respx.post("https://test_shop.oekobox-online.de/json/logon").mock(
            return_value=httpx.Response(401, json={"error": "Invalid credentials"})
        )

        with pytest.raises(OekoboxAuthenticationError):
            await client.login()

    @pytest.mark.asyncio
    @respx.mock
    async def test_validation_error(self):
        """Test validation error handling."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        # Mock response with invalid data structure
        respx.get("https://test_shop.oekobox-online.de/json/groups").mock(
            return_value=httpx.Response(200, json=[{"invalid": "data"}])
        )

        with pytest.raises(OekoboxValidationError):
            await client.get_groups()

    @pytest.mark.asyncio
    @respx.mock
    async def test_logout(self):
        """Test logout functionality."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        respx.post("https://test_shop.oekobox-online.de/json/logout").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.logout()
        assert client.session_id is None
