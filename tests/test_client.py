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
    Address,
    DDate,
    Delivery,
    Group,
    Item,
    Order,
    ShopUrl,
    Tour,
    UserInfo,
    XUnit,
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
    async def test_request_http_error_404(self):
        """Test HTTP 404 error handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxAPIError, match="HTTP 404: Not found"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_http_error_409(self):
        """Test HTTP 409 error handling."""
        respx.get("http://example.com/api/test").mock(
            return_value=httpx.Response(409, text="Conflict")
        )

        async with OekoboxClient("test_shop", "user", "pass") as client:
            with pytest.raises(OekoboxAPIError, match="HTTP 409: Conflict error"):
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
            with pytest.raises(OekoboxConnectionError, match="Request failed"):
                await client._request("GET", "http://example.com/api/test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_logon_success(self):
        """Test successful logon."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logon2").mock(
            return_value=httpx.Response(
                200,
                json={
                    "result": "ok",
                    "pcgifversion": "1.0",
                    "shopversion": "2.1",
                },
            )
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            response = await client.logon()
            assert response["result"] == "ok"
            assert response["pcgifversion"] == "1.0"
            assert response["shopversion"] == "2.1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_logon_failure(self):
        """Test logon failure."""
        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/logon2").mock(
            return_value=httpx.Response(200, json={"result": "wrong_password"})
        )

        async with OekoboxClient("test_shop", "testuser", "wrongpass") as client:
            with pytest.raises(
                OekoboxAuthenticationError,
                match="Wrong password",
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
            response = await client.logout()
            assert response["result"] == "ok"
            assert client.session_id is None

    @pytest.mark.asyncio
    @respx.mock
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/groups4").mock(
            return_value=httpx.Response(200, json=mock_response)
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
    @respx.mock
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/items").mock(
            return_value=httpx.Response(200, json=mock_response)
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
    @respx.mock
    async def test_get_item(self):
        """Test getting a specific item."""
        # get_item expects a raw list response (not wrapped in DataList format)
        mock_response = [1, "Apple", 2.50, "kg", "Fresh red apples", 1, 7.0]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/item/1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            item = await client.get_item(1)
            assert isinstance(item, Item)
            assert item.id == 1
            assert item.name == "Apple"
            assert item.price == 2.50
            assert item.unit == "kg"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_itemlist(self):
        """Test getting item list."""
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/itemlist16").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            result = await client.get_itemlist([1, 2])
            # Should return mixed types: Items and XUnits
            items = [r for r in result if isinstance(r, Item)]
            xunits = [r for r in result if isinstance(r, XUnit)]
            assert len(items) == 2
            assert len(xunits) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_to_cart(self):
        """Test adding item to cart."""
        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/add").mock(
            return_value=httpx.Response(
                200, json={"result": "ok", "message": "Item added"}
            )
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            response = await client.add_to_cart(
                item_id=1, amount=2.0, note="Extra fresh"
            )
            assert response["result"] == "ok"

    @pytest.mark.asyncio
    @respx.mock
    async def test_remove_from_cart(self):
        """Test removing item from cart."""
        respx.post("https://oekobox-online.de/v3/shop/test_shop/api/cart/remove").mock(
            return_value=httpx.Response(
                200, json={"result": "ok", "message": "Item removed"}
            )
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            response = await client.remove_from_cart(item_id=1)
            assert response["result"] == "ok"

    @pytest.mark.asyncio
    @respx.mock
    async def test_show_cart(self):
        """Test showing cart contents."""
        mock_response = [
            {
                "type": "CartItem",
                "data": [
                    [1, 2.0, 5.0],
                    [2, 1.0, 1.8],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/cart/show").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            cart_items = await client.show_cart()
            assert len(cart_items) == 2

    @pytest.mark.asyncio
    @respx.mock
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

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/orders").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            orders = await client.get_orders()
            assert len(orders) == 2
            assert isinstance(orders[0], Order)
            assert orders[0].id == 1
            assert orders[0].ddate == "2024-01-15"

    @pytest.mark.asyncio
    @respx.mock
    async def test_new_order(self):
        """Test creating new order."""
        respx.post(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/neworder"
        ).mock(return_value=httpx.Response(200, json={"result": "ok", "order_id": 123}))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            response = await client.new_order(
                delivery_date="2024-01-20",
                tour_id=1,
                customer_note="Please deliver after 5pm",
            )
            assert response["result"] == "ok"
            assert response["order_id"] == 123

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_tour(self):
        """Test getting tour information."""
        mock_response = [
            {
                "type": "Tour",
                "data": [
                    [
                        1,
                        "Morning Route",
                        "Early morning deliveries",
                        "12345,12346",
                        "Handle with care",
                    ],
                    [0],
                ],
            },
            {
                "type": "DDate",
                "data": [
                    [1, 1, "2024-01-15", 3, "2024-01-14", 1, "Pack early", 5, 8],
                    [0],
                ],
            },
            {
                "type": "Delivery",
                "data": [
                    [
                        1,
                        100,
                        0,
                        "",
                        1,
                        "Ring doorbell",
                        "Use back entrance",
                        "",
                        "BOX001",
                    ],
                    [0],
                ],
            },
            {
                "type": "Address",
                "data": [
                    [100, "", "Smith", "John", "123 Main St", "Berlin", "12345"],
                    [0],
                ],
            },
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/tour30/1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            result = await client.get_tour(1)
            tours = [r for r in result if isinstance(r, Tour)]
            ddates = [r for r in result if isinstance(r, DDate)]
            deliveries = [r for r in result if isinstance(r, Delivery)]
            addresses = [r for r in result if isinstance(r, Address)]

            assert len(tours) == 1
            assert len(ddates) == 1
            assert len(deliveries) == 1
            assert len(addresses) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_info(self):
        """Test getting user information."""
        mock_response = [
            {
                "type": "UserInfo",
                "data": [
                    ["AUTH", 123, "Dear", "John", "Smith", "0", "0", "0", "0", 0],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/user20").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            user_info = await client.get_user_info()
            assert len(user_info) == 1
            assert isinstance(user_info[0], UserInfo)
            assert user_info[0].authentication_state == "AUTH"
            assert user_info[0].user_id == 123

    @pytest.mark.asyncio
    @respx.mock
    async def test_search(self):
        """Test search functionality."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Apple Juice", 3.50, "bottle", "Organic apple juice", 2, 7.0],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            results = await client.search("apple")
            assert len(results) == 1
            assert isinstance(results[0], Item)
            assert "Apple" in results[0].name

    @pytest.mark.asyncio
    @respx.mock
    async def test_find_shop(self):
        """Test finding shops by location."""
        mock_response = [
            {
                "type": "ShopUrl",
                "version": "4",
                "data": [
                    [
                        "Organic Market Berlin",
                        "http://example.com",
                        "http://example.com",
                        "http://example.com",
                        "",
                        "berlin",
                        0,
                        52.530008,
                        13.414954,
                        1,
                    ],
                    [
                        "Munich Organic",
                        "http://example.com",
                        "http://example.com",
                        "http://example.com",
                        "",
                        "munich",
                        0,
                        48.147154,
                        11.586124,
                        1,
                    ],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/findshop").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            shops = await client.find_shop(52.5, 13.4)
            assert len(shops) == 2
            assert isinstance(shops[0], ShopUrl)
            assert shops[0].lat == 52.530008
            assert shops[0].lng == 13.414954
            assert shops[0].display_name == "Organic Market Berlin"
            assert shops[0].sysname == "berlin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_request_with_datalist_response(self):
        """Test _api_request method with DataList response."""
        mock_response = [
            {
                "type": "Group",
                "data": [
                    [1, "Test Group", "Description", 10],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/test").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            result = await client._api_request("test")
            assert len(result) == 1
            assert isinstance(result[0], Group)
            assert result[0].id == 1
            assert result[0].name == "Test Group"

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_request_with_non_list_response(self):
        """Test _api_request method with non-list response."""
        mock_response = {"result": "ok", "message": "Success"}

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/test").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            result = await client._api_request("test")
            assert result == mock_response

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_assortments(self):
        """Test getting assortments."""
        mock_response = [
            {
                "type": "Assortment",
                "data": [
                    [
                        1,
                        "Fruit Box Small",
                        "A small box with seasonal fruits",
                        2,
                        15.99,
                        1,
                        "pic123",
                        "2024-01-01T00:00:00",
                        "2024-12-31T23:59:59",
                        5,
                        10,
                        1,
                        "Perfect for couples",
                        0,
                        1,
                        "thumb123",
                    ],
                    [
                        2,
                        "Veggie Box Large",
                        "A large box with seasonal vegetables",
                        4,
                        29.99,
                        1,
                        "pic456",
                        "2024-01-01T00:00:00",
                        "2024-12-31T23:59:59",
                        10,
                        10,
                        2,
                        "Great for families",
                        0,
                        2,
                        "thumb456",
                    ],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/assortments4").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            from pyoekoboxonline.models import Assortment

            assortments = await client.get_assortments()
            assert len(assortments) == 2
            assert isinstance(assortments[0], Assortment)
            assert assortments[0].id == 1
            assert assortments[0].name == "Fruit Box Small"
            assert assortments[0].person_count == 2
            assert assortments[0].price == 15.99
            assert assortments[0].item_count == 5
            assert assortments[1].id == 2
            assert assortments[1].name == "Veggie Box Large"
            assert assortments[1].person_count == 4

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_with_fuzzy(self):
        """Test search functionality with fuzzy parameter."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Apple Juice", 3.50, "bottle", "Organic apple juice", 2, 7.0],
                    [2, "Appel Pie", 5.00, "piece", "Homemade apple pie", 3, 7.0],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            results = await client.search("apel", fuzzy=True)

            # Verify the request was made with correct parameters
            request = respx.calls.last.request
            assert "q=apel" in str(request.url)
            assert "fuzzy=2" in str(request.url)
            assert "qe=1" in str(request.url)
            assert "fields=3" in str(request.url)

            assert len(results) == 2
            assert isinstance(results[0], Item)

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_with_limit(self):
        """Test search functionality with limit parameter."""
        mock_response = [
            {
                "type": "Item",
                "data": [
                    [1, "Apple Juice", 3.50, "bottle", "Organic apple juice", 2, 7.0],
                    [0],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/shop/test_shop/api/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            await client.search("apple", limit=5)

            # Verify the max parameter was used instead of limit
            request = respx.calls.last.request
            assert "max=5" in str(request.url)
            assert "limit" not in str(request.url).lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_pause_with_date_format(self):
        """Test adding pause with proper date format parameter."""
        import datetime

        mock_response = [
            {
                "type": "ShopDate",
                "data": [[1, "2024-01-15", 1, "Monday", 5], [0]],
            },
            {
                "type": "Pause",
                "data": [[1, "2024-02-01", "2024-02-07", 0], [0]],
            },
        ]

        respx.post(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/addpause"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            from_date = datetime.datetime(2024, 2, 1)
            to_date = datetime.datetime(2024, 2, 7)

            result = await client.add_pause(from_date, to_date, auto_cancel=True)

            # Verify the request was made with correct parameters
            request = respx.calls.last.request
            body = request.content.decode()
            assert "BusinessEntity.DATEFORMAT=iso8601d" in body
            assert "von=2024-02-01" in body
            assert "bis=2024-02-07" in body
            assert "autocancel=1" in body

            # Verify the response was parsed correctly
            from pyoekoboxonline.models import Pause, ShopDate

            shop_dates = [r for r in result if isinstance(r, ShopDate)]
            pauses = [r for r in result if isinstance(r, Pause)]
            assert len(shop_dates) == 1
            assert len(pauses) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_drop_pause(self):
        """Test dropping/removing a pause."""
        mock_response = [
            {
                "type": "ShopDate",
                "data": [[1, "2024-01-15", 1, "Monday", 5], [0]],
            },
            {
                "type": "Pause",
                "data": [
                    # Empty pause list after dropping
                    [0]
                ],
            },
        ]

        respx.post(
            "https://oekobox-online.de/v3/shop/test_shop/api/client/droppause"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with OekoboxClient("test_shop", "testuser", "testpass") as client:
            result = await client.drop_pause(pause_id=123)

            # Verify the request was made with correct parameter
            request = respx.calls.last.request
            body = request.content.decode()
            assert "lpid=123" in body

            # Verify the response was parsed correctly
            from pyoekoboxonline.models import Pause, ShopDate

            shop_dates = [r for r in result if isinstance(r, ShopDate)]
            pauses = [r for r in result if isinstance(r, Pause)]
            assert len(shop_dates) == 1
            # Pauses list should be empty after dropping
            assert len(pauses) == 0
