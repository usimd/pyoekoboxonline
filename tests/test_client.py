"""Tests for the Ökobox Online API client."""

from datetime import datetime

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
    async def test_login_backward_compatibility(self):
        """Test that login() calls logon() for backward compatibility."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logon").mock(
            return_value=httpx.Response(200, json={"action": "Logon", "result": "ok"})
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.login()
            assert isinstance(user_info, UserInfo)
            assert user_info.username == "testuser"

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
    async def test_get_items(self):
        """Test getting items."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Organic Apples", 3.99, "kg", "Fresh organic apples", "1"],
                    [2, "Organic Bananas", 2.49, "kg", "Fresh organic bananas", "1"],
                    [0],  # Terminating entry
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/items1/-1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            items = await client.get_items()
            assert len(items) == 2
            assert items[0].id == "1"
            assert items[0].name == "Organic Apples"
            assert items[0].price == 3.99
            assert items[0].description == "Fresh organic apples"
            assert items[0].group_id == "1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_delivery_dates(self):
        """Test getting delivery dates."""
        mock_response = [
            {
                "type": "ShopDate",
                "data": [
                    [1, "confirmed", "2023-12-25T10:00:00Z"],
                    [2, "available", "2023-12-26T10:00:00Z"],
                    [0],  # Terminating entry
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/dates1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            dates = await client.get_delivery_dates()
            assert len(dates) == 2
            assert isinstance(dates[0].date, datetime)
            assert dates[0].is_available is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_to_cart_success(self):
        """Test adding item to cart successfully."""
        mock_response = [
            {
                "type": "CartItem",
                "data": [
                    [1, 2.0, "kg", 3.99, "Fresh apples"],
                    [0],  # Terminating entry
                ],
            }
        ]

        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/add").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            cart_items = await client.add_to_cart("1", 2.0, "kg", "Fresh apples")
            assert len(cart_items) == 1
            assert cart_items[0].item_id == "1"
            assert cart_items[0].quantity == 2.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_to_cart_no_delivery_date(self):
        """Test adding to cart without delivery date selected."""
        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/add").mock(
            return_value=httpx.Response(200, json={"result": "no_ddate"})
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            with pytest.raises(
                OekoboxValidationError, match="delivery date must be selected"
            ):
                await client.add_to_cart("1", 1.0)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_cart(self):
        """Test getting cart contents."""
        mock_response = [
            {
                "type": "CartItem",
                "data": [
                    [1, 2.0, "kg", 3.99, "Fresh apples"],
                    [2, 1.0, "piece", 1.99, "Organic bread"],
                    [0],  # Terminating entry
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/cart/show").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            cart_items = await client.get_cart()
            assert len(cart_items) == 2
            assert cart_items[0].item_id == "1"
            assert cart_items[0].quantity == 2.0
            assert cart_items[1].item_id == "2"
            assert cart_items[1].quantity == 1.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_clear_cart(self):
        """Test clearing the cart."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/resetcart"
        ).mock(return_value=httpx.Response(200, json={"result": "ok"}))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            await client.clear_cart()  # Should not raise an exception

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_favourite(self):
        """Test adding item to favourites."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/addfavourites"
        ).mock(return_value=httpx.Response(200, json={"result": "ok"}))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            await client.add_favourite("item_123")  # Should not raise an exception

    @pytest.mark.asyncio
    @respx.mock
    async def test_remove_favourite(self):
        """Test removing item from favourites."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/dropfavourites"
        ).mock(return_value=httpx.Response(200, json={"result": "ok"}))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            await client.remove_favourite("item_123")  # Should not raise an exception

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_customer_info(self):
        """Test getting customer info."""
        async with OekoboxClient(
            "test_shop", "testuser@example.com", "testpass"
        ) as client:
            customer_info = await client.get_customer_info()
            assert isinstance(customer_info, CustomerInfo)
            assert customer_info.id == "testuser@example.com"
            assert customer_info.user_info.username == "testuser@example.com"
            assert customer_info.user_info.email == "testuser@example.com"

    @pytest.mark.asyncio
    async def test_client_properties(self):
        """Test client property methods."""
        client = OekoboxClient("test_shop", "user", "pass")
        assert client.api_base_url == "https://oekobox-online.de/v3/shop/test_shop/api"

    @pytest.mark.asyncio
    @respx.mock
    async def test_error_handling_empty_response(self):
        """Test handling of empty or invalid JSON responses."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(200, text="OK")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            response = await client._request("GET", "http://example.com/api/test")
            assert response["result"] == "ok"
            assert response["response_text"] == "OK"

    # Advanced test cases (merged from test_client_advanced.py)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_item_by_id_success(self):
        """Test getting a specific item by ID."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [123, "Organic Apples", 3.99, "kg", "Fresh organic apples", "1"],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/items1/-1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            items = await client.get_items()
            # Find the item with ID 123
            item = next((item for item in items if item.id == "123"), None)
            assert item is not None
            assert item.id == "123"
            assert item.name == "Organic Apples"
            assert item.price == 3.99

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_item_not_found(self):
        """Test getting a non-existent item."""
        mock_response = [
            {
                "type": "Item",
                "data": [[456, "Other Item", 2.99, "kg", "Other item", "1"], [0]],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/items1/-1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            items = await client.get_items()
            # Try to find item with ID 999 - should not exist
            item = next((item for item in items if item.id == "999"), None)
            assert item is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_remove_from_cart_by_item_id(self):
        """Test removing item from cart by item ID."""
        mock_response = [
            {
                "type": "CartItem",
                "data": [[2, 1.0, "piece", 1.99, "Remaining item"], [0]],
            }
        ]

        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/remove").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            cart_items = await client.remove_from_cart(item_id="1")
            assert len(cart_items) == 1
            assert cart_items[0].item_id == "2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_remove_from_cart_by_position(self):
        """Test removing item from cart by position."""
        mock_response = [
            {
                "type": "CartItem",
                "data": [[2, 1.0, "piece", 1.99, "Remaining item"], [0]],
            }
        ]

        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/remove").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            cart_items = await client.remove_from_cart(position=0)
            assert len(cart_items) == 1

    @pytest.mark.asyncio
    async def test_remove_from_cart_no_parameters(self):
        """Test that remove_from_cart raises error when no parameters provided."""
        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            with pytest.raises(
                ValueError, match="Either item_id or position must be provided"
            ):
                await client.remove_from_cart()

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_orders_success(self):
        """Test getting customer orders."""
        mock_response = [
            {
                "type": "ShopDate",
                "data": [
                    [
                        101,
                        "confirmed",
                        "2023-12-25T10:00:00Z",
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        19.98,
                    ],
                    [
                        102,
                        "delivered",
                        "2023-12-20T10:00:00Z",
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        15.50,
                    ],
                    [-1],  # Terminating entry
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/dates1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            orders = await client.get_orders()
            assert len(orders) == 2
            assert orders[0].id == "101"
            assert orders[0].status == "confirmed"
            assert orders[0].total == 19.98

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_order_by_id(self):
        """Test getting a specific order by ID."""
        mock_response = [
            {"type": "Order", "data": [[101, "2023-12-25T10:00:00Z", "confirmed"]]}
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/order2/101").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            order = await client.get_order("101")
            assert order.id == "101"
            assert order.status == "confirmed"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_order_not_found(self):
        """Test getting a non-existent order."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/order2/999").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            with pytest.raises(OekoboxValidationError, match="Order not found: 999"):
                await client.get_order("999")

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_subscriptions_success(self):
        """Test getting customer subscriptions."""
        # Mock the successful primary endpoint response
        mock_subscriptions = [
            {
                "id": "1",
                "customer_id": "testuser",
                "frequency": "weekly",
                "is_active": True,
            },
            {
                "id": "2",
                "customer_id": "testuser",
                "frequency": "monthly",
                "is_active": True,
            },
        ]

        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/subscriptions"
        ).mock(return_value=httpx.Response(200, json=mock_subscriptions))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            subscriptions = await client.get_subscriptions()
            assert len(subscriptions) == 2
            assert subscriptions[0].id == "1"
            assert subscriptions[0].frequency == "weekly"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_subscriptions_fallback_to_empty(self):
        """Test that get_subscriptions returns empty list when endpoints fail."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/subscriptions"
        ).mock(return_value=httpx.Response(404, text="Not Found"))
        respx.get("https://oekobox-online.de/v3/shop/test_shop/dates1").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            subscriptions = await client.get_subscriptions()
            assert subscriptions == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_favourites_success(self):
        """Test getting customer favourites."""
        # Mock the successful primary endpoint response
        mock_favourites = [
            {"customer_id": "testuser", "item_id": "123"},
            {"customer_id": "testuser", "item_id": "456"},
        ]

        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/favourites"
        ).mock(return_value=httpx.Response(200, json=mock_favourites))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            favourites = await client.get_favourites()
            assert len(favourites) == 2
            assert favourites[0].item_id == "123"
            assert favourites[1].item_id == "456"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_favourites_fallback_to_empty(self):
        """Test that get_favourites returns empty list when endpoints fail."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/favourites"
        ).mock(return_value=httpx.Response(404, text="Not Found"))
        respx.get("https://oekobox-online.de/v3/shop/test_shop/dates1").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            favourites = await client.get_favourites()
            assert favourites == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_clear_cart_with_empty_response(self):
        """Test clearing cart when API returns empty response."""
        respx.get(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/resetcart"
        ).mock(return_value=httpx.Response(200, json={"result": ""}))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            await client.clear_cart()  # Should not raise exception

    @pytest.mark.asyncio
    @respx.mock
    async def test_delivery_dates_fallback_endpoint(self):
        """Test delivery dates with fallback to base URL endpoint."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/dates1").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        mock_response = [
            {
                "type": "ShopDate",
                "data": [[1, "available", "2023-12-25T10:00:00Z"], [0]],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/dates1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            dates = await client.get_delivery_dates()
            assert len(dates) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_available_shops_with_invalid_coordinates(self):
        """Test shop list parsing with invalid coordinates."""
        mock_response = """[-1,-1,"Invalid Shop",-1,-1,"invalid_shop"]
[52.520008,13.404954,"Valid Shop",52.530008,13.414954,"valid_shop"]"""

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, text=mock_response)
        )

        shops = await OekoboxClient.get_available_shops()
        # The client currently doesn't filter invalid coordinates, so both shops are returned
        assert len(shops) == 2
        assert shops[0].id == "invalid_shop"
        assert shops[0].name == "Invalid Shop"
        assert shops[0].latitude == -1.0
        assert shops[1].id == "valid_shop"
        assert shops[1].name == "Valid Shop"
