"""Tests for the Ökobox Online API client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxValidationError,
)
from pyoekoboxonline.models import (
    CartItem,
    CustomerInfo,
    DDate,
    Favourite,
    Group,
    Item,
    Shop,
    SubGroup,
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

    def test_client_initialization_with_custom_url(self):
        """Test client initialization with custom base URL."""
        client = OekoboxClient(
            shop_id="test_shop",
            username="testuser",
            password="testpass",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    def test_client_initialization_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass", timeout=60.0
        )
        assert client.timeout == 60.0

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

        url = client._build_url("/api/items")
        assert url == "https://oekobox-online.de/v3/shop/test_shop/api/items"

        url = client._build_url("logon")  # Test without leading slash
        assert url == "https://oekobox-online.de/v3/shop/test_shop/logon"

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
        """Test successful login with cookie session."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_response = {
            "id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
        }

        # Mock login endpoint with cookie response using headers
        respx.get("https://oekobox-online.de/v3/shop/test_shop/logon").mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={"Set-Cookie": "OOSESSION=session_abc123; Path=/; HttpOnly"},
            )
        )

        user_info = await client.login()
        assert isinstance(user_info, UserInfo)
        assert user_info.username == "testuser"
        assert client.session_id == "session_abc123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_login_no_json_response(self):
        """Test login with no JSON response creates minimal user info."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        # Mock login endpoint with plain text response and cookie header
        respx.get("https://oekobox-online.de/v3/shop/test_shop/logon").mock(
            return_value=httpx.Response(
                200,
                text="Login successful",
                headers={"Set-Cookie": "OOSESSION=session_abc123; Path=/; HttpOnly"},
            )
        )

        user_info = await client.login()
        assert isinstance(user_info, UserInfo)
        assert user_info.username == "testuser"
        assert user_info.is_active is True
        assert client.session_id == "session_abc123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_login_no_cookie(self):
        """Test login failure when no session cookie is returned."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        # Mock login endpoint without cookie
        respx.get("https://oekobox-online.de/v3/shop/test_shop/logon").mock(
            return_value=httpx.Response(200, json={})
        )

        with pytest.raises(OekoboxAuthenticationError, match="no session ID received"):
            await client.login()

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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
            return_value=httpx.Response(200, json=mock_groups)
        )

        groups = await client.get_groups()
        assert len(groups) == 2
        assert isinstance(groups[0], Group)
        assert groups[0].id == "fruits"
        assert groups[1].name == "Vegetables"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_groups_wrapped_response(self):
        """Test groups retrieval with wrapped response."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_response = {
            "groups": [
                {"id": "fruits", "name": "Fresh Fruits"},
                {"id": "vegetables", "name": "Vegetables"},
            ]
        }

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        groups = await client.get_groups()
        assert len(groups) == 2
        assert isinstance(groups[0], Group)
        assert groups[0].id == "fruits"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_subgroups_success(self):
        """Test successful subgroups retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_subgroups = [
            {"id": "apples", "name": "Apples", "group_id": "fruits"},
            {"id": "oranges", "name": "Oranges", "group_id": "fruits"},
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/subgroup").mock(
            return_value=httpx.Response(200, json=mock_subgroups)
        )

        subgroups = await client.get_subgroups(group_id="fruits")
        assert len(subgroups) == 2
        assert isinstance(subgroups[0], SubGroup)
        assert subgroups[0].id == "apples"
        assert subgroups[0].group_id == "fruits"

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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/items").mock(
            return_value=httpx.Response(200, json=mock_items)
        )

        items = await client.get_items()
        assert len(items) == 1
        assert isinstance(items[0], Item)
        assert items[0].name == "Organic Apples"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_item_success(self):
        """Test successful single item retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_item = {
            "id": "item_1",
            "name": "Organic Apples",
            "price": 3.99,
            "is_available": True,
        }

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/item").mock(
            return_value=httpx.Response(200, json=mock_item)
        )

        item = await client.get_item("item_1")
        assert isinstance(item, Item)
        assert item.name == "Organic Apples"
        assert item.id == "item_1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_items_success(self):
        """Test successful item search."""
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/search").mock(
            return_value=httpx.Response(200, json=mock_items)
        )

        items = await client.search_items("apple")
        assert len(items) == 1
        assert isinstance(items[0], Item)
        assert items[0].name == "Organic Apples"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_cart_success(self):
        """Test successful cart retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        mock_cart = [
            {
                "item_id": "item_1",
                "quantity": 2.0,
                "unit_price": 3.99,
                "total_price": 7.98,
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/cart/show").mock(
            return_value=httpx.Response(200, json=mock_cart)
        )

        cart_items = await client.get_cart()
        assert len(cart_items) == 1
        assert isinstance(cart_items[0], CartItem)
        assert cart_items[0].item_id == "item_1"
        assert cart_items[0].quantity == 2.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_to_cart_success(self):
        """Test successful add to cart."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/add").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.add_to_cart("item_1", 2.0)
        # No exception should be raised

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_available_shops_success(self):
        """Test successful available shops retrieval."""
        # Mock the shop list response in JavaScript array format
        mock_js_content = """[52.5200,13.4050,"Berlin Organic Market",52.5300,13.4150,"berlin_shop"]
[48.1351,11.5820,"Munich Bio Store",48.1400,11.5900,"munich_shop"]
[-1,-1,"Invalid Shop",50.0000,10.0000,"invalid_shop"]"""

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, text=mock_js_content)
        )

        shops = await OekoboxClient.get_available_shops()
        assert len(shops) == 3
        assert isinstance(shops[0], Shop)
        assert shops[0].id == "berlin_shop"
        assert shops[0].name == "Berlin Organic Market"
        assert shops[0].latitude == 52.5200

        # Test shop with invalid primary coordinates using secondary
        invalid_shop = next(shop for shop in shops if shop.id == "invalid_shop")
        assert invalid_shop.latitude == 50.0000
        assert invalid_shop.longitude == 10.0000

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_delivery_dates_success(self):
        """Test successful delivery dates retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        mock_dates = [
            {
                "date": "2023-10-15T00:00:00Z",
                "is_available": True,
                "delivery_slots": ["morning", "afternoon"],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/dates").mock(
            return_value=httpx.Response(200, json=mock_dates)
        )

        dates = await client.get_delivery_dates()
        assert len(dates) == 1
        assert isinstance(dates[0], DDate)
        assert dates[0].is_available is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        mock_user = {
            "id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
        }

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user").mock(
            return_value=httpx.Response(200, json=mock_user)
        )

        user_info = await client.get_user_info()
        assert isinstance(user_info, UserInfo)
        assert user_info.username == "testuser"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_customer_info_success(self):
        """Test successful customer info retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        mock_customer = {
            "id": "customer_123",
            "user_info": {"id": "user_123", "username": "testuser"},
        }

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/client/state").mock(
            return_value=httpx.Response(200, json=mock_customer)
        )

        customer_info = await client.get_customer_info()
        assert isinstance(customer_info, CustomerInfo)
        assert customer_info.id == "customer_123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_connection_error(self):
        """Test connection error handling."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        respx.get("https://oekobox-online.de/v3/shop/test_shop/logon").mock(
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/logon").mock(
            return_value=httpx.Response(401, json={"error": "Invalid credentials"})
        )

        with pytest.raises(OekoboxAuthenticationError):
            await client.login()

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error_with_json(self):
        """Test API error handling with JSON response."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
            return_value=httpx.Response(400, json={"message": "Bad request"})
        )

        with pytest.raises(OekoboxAPIError, match="Bad request"):
            await client.get_groups()

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error_without_json(self):
        """Test API error handling without JSON response."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        with pytest.raises(OekoboxAPIError, match="HTTP 500"):
            await client.get_groups()

    @pytest.mark.asyncio
    @respx.mock
    async def test_validation_error(self):
        """Test validation error handling."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )

        # Mock response with invalid data structure
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/logout").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await client.logout()
        assert client.session_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_logout_no_session(self):
        """Test logout when no session exists."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = None

        # logout should not make any request if no session_id
        await client.logout()
        assert client.session_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_authenticated_request_includes_session_and_header(self):
        """Test that authenticated requests include session ID and auth header."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session_123"

        # Track the actual request
        request_tracker = []

        def track_request(request):
            request_tracker.append(
                {"params": dict(request.url.params), "headers": dict(request.headers)}
            )
            return httpx.Response(
                200,
                json={
                    "id": "user_123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "is_active": True,
                },
            )

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user").mock(
            side_effect=track_request
        )

        user_info = await client.get_user_info()
        assert isinstance(user_info, UserInfo)

        # Verify the request included session and auth header
        assert len(request_tracker) == 1
        request_data = request_tracker[0]
        assert request_data["params"]["x-oekobox-sid"] == "test_session_123"
        assert request_data["headers"]["x-oo-auth"] == "1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_non_authenticated_request_no_auth_header(self):
        """Test that non-authenticated requests don't include auth header."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session_123"

        # Track the actual request
        request_tracker = []

        def track_request(request):
            request_tracker.append(
                {"params": dict(request.url.params), "headers": dict(request.headers)}
            )
            return httpx.Response(200, json=[{"id": "fruits", "name": "Fresh Fruits"}])

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups").mock(
            side_effect=track_request
        )

        groups = await client.get_groups()
        assert len(groups) == 1

        # Verify the request included session but no auth header
        assert len(request_tracker) == 1
        request_data = request_tracker[0]
        assert request_data["params"]["x-oekobox-sid"] == "test_session_123"
        assert "x-oo-auth" not in request_data["headers"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_favourites_success(self):
        """Test successful favourites retrieval."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        mock_favourites = [
            {
                "customer_id": "customer_123",
                "item_id": "item_1",
                "added_date": "2023-10-15T00:00:00Z",
            }
        ]

        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/favourites"
        ).mock(return_value=httpx.Response(200, json=mock_favourites))

        favourites = await client.get_favourites()
        assert len(favourites) == 1
        assert isinstance(favourites[0], Favourite)
        assert favourites[0].item_id == "item_1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_favourite_success(self):
        """Test successful favourite addition."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        respx.post(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/addfavourites"
        ).mock(return_value=httpx.Response(200, json={"success": True}))

        await client.add_favourite("item_1")
        # No exception should be raised

    @pytest.mark.asyncio
    @respx.mock
    async def test_remove_favourite_success(self):
        """Test successful favourite removal."""
        client = OekoboxClient(
            shop_id="test_shop", username="testuser", password="testpass"
        )
        client.session_id = "test_session"

        respx.post(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/dropfavourites"
        ).mock(return_value=httpx.Response(200, json={"success": True}))

        await client.remove_favourite("item_1")
        # No exception should be raised
