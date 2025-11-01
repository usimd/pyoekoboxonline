"""Tests for static methods that don't require authentication."""

import httpx
import pytest
import respx

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.models import Shop, ShopUrl


class TestStaticMethods:
    """Test cases for static methods."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_find_shop_static(self):
        """Test finding shops by location as a static method."""
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

        # Call as static method without creating a client instance
        shops = await OekoboxClient.find_shop(52.5, 13.4)
        assert len(shops) == 2
        assert isinstance(shops[0], ShopUrl)
        assert shops[0].lat == 52.530008
        assert shops[0].lng == 13.414954
        assert shops[0].display_name == "Organic Market Berlin"
        assert shops[0].sysname == "berlin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_shop_info_static(self):
        """Test getting shop information as a static method."""
        mock_response = [
            [
                "test_shop",
                "Test Shop",
                "A test shop",
                "https://example.com",
                "test@example.com",
                "123-456-7890",
                "Test Address",
                "Berlin",
                "10115",
                "Germany",
                52.5200,
                13.4050,
                1,
            ],
            [
                "another_shop",
                "Another Shop",
                "Another test shop",
                "https://example2.com",
                "test2@example.com",
                "987-654-3210",
                "Another Address",
                "Munich",
                "80331",
                "Germany",
                48.1351,
                11.5820,
                1,
            ],
        ]

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # Call as static method without creating a client instance
        shops = await OekoboxClient.get_shop_info()
        assert len(shops) == 2
        assert isinstance(shops[0], Shop)

    @pytest.mark.asyncio
    @respx.mock
    async def test_find_shop_with_custom_timeout(self):
        """Test finding shops with custom timeout."""
        mock_response = [
            {
                "type": "ShopUrl",
                "version": "4",
                "data": [
                    [
                        "Test Shop",
                        "http://example.com",
                        "http://example.com",
                        "http://example.com",
                        "",
                        "test",
                        0,
                        52.0,
                        13.0,
                        1,
                    ],
                ],
            }
        ]

        respx.get("https://oekobox-online.de/v3/findshop").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # Call with custom timeout
        shops = await OekoboxClient.find_shop(52.0, 13.0, timeout=60.0)
        assert len(shops) == 1
        assert isinstance(shops[0], ShopUrl)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_shop_info_with_custom_timeout(self):
        """Test getting shop info with custom timeout."""
        mock_response = [
            [
                "test_shop",
                "Test Shop",
                "Description",
                "https://example.com",
                "test@example.com",
                "123-456",
                "Address",
                "City",
                "12345",
                "Country",
                52.0,
                13.0,
                1,
            ],
        ]

        respx.get("https://oekobox-online.eu/v3/shoplist.js.jsp").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # Call with custom timeout
        shops = await OekoboxClient.get_shop_info(timeout=60.0)
        assert len(shops) == 1
        assert isinstance(shops[0], Shop)
