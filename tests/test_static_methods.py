"""Tests for static methods that don't require authentication."""

import pytest
from aioresponses import aioresponses

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.models import Shop, ShopUrl


class TestStaticMethods:
    """Test cases for static methods."""

    @pytest.mark.asyncio
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

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/findshop?lat=52.5&lng=13.4",
                payload=mock_response,
            )

            # Call as static method without creating a client instance
            shops = await OekoboxClient.find_shop(52.5, 13.4)
            assert len(shops) == 2
            assert isinstance(shops[0], ShopUrl)
            assert shops[0].lat == 52.530008
            assert shops[0].lng == 13.414954
            assert shops[0].display_name == "Organic Market Berlin"

    @pytest.mark.asyncio
    async def test_get_shop_info_static(self):
        """Test getting shop information as a static method."""
        # Mock the raw API response (array of arrays)
        mock_response = [
            [
                52.5200,
                13.4050,
                "Berlin Organic Market",
                52.5300,
                13.4150,
                "berlin_shop",
            ],
            [48.1351, 11.5820, "Munich Bio Store", 48.1400, 11.5900, "munich_shop"],
        ]

        with aioresponses() as m:
            m.get("https://oekobox-online.eu/v3/shoplist.js.jsp", payload=mock_response)

            # Call as static method without creating a client instance
            shops = await OekoboxClient.get_shop_info()
            assert len(shops) == 2
            assert isinstance(shops[0], Shop)
            assert shops[0].name == "Berlin Organic Market"
            assert shops[0].id == "berlin_shop"
            assert shops[0].latitude == 52.5200
            assert shops[0].longitude == 13.4050

    @pytest.mark.asyncio
    async def test_find_shop_with_params(self):
        """Test finding shops with specific latitude/longitude."""
        mock_response = [
            {
                "type": "ShopUrl",
                "version": "4",
                "data": [
                    [
                        "Local Organic Shop",
                        "http://example.com",
                        "http://example.com",
                        "http://example.com",
                        "",
                        "local_shop",
                        0,
                        50.9375,
                        6.9603,
                        1,
                    ],
                ],
            }
        ]

        with aioresponses() as m:
            # Check that the correct URL with parameters is called
            m.get(
                "https://oekobox-online.de/v3/findshop?lat=50.9375&lng=6.9603",
                payload=mock_response,
            )

            shops = await OekoboxClient.find_shop(50.9375, 6.9603)
            assert len(shops) == 1
            assert shops[0].display_name == "Local Organic Shop"

    @pytest.mark.asyncio
    async def test_get_shop_info_empty_result(self):
        """Test shop info with empty result."""
        with aioresponses() as m:
            m.get("https://oekobox-online.eu/v3/shoplist.js.jsp", payload=[])

            shops = await OekoboxClient.get_shop_info()
            assert len(shops) == 0

    @pytest.mark.asyncio
    async def test_find_shop_empty_result(self):
        """Test finding shops with no results."""
        mock_response = [
            {
                "type": "ShopUrl",
                "version": "4",
                "data": [],
            }
        ]

        with aioresponses() as m:
            m.get(
                "https://oekobox-online.de/v3/findshop?lat=0.0&lng=0.0",
                payload=mock_response,
            )

            shops = await OekoboxClient.find_shop(0.0, 0.0)
            assert len(shops) == 0

    @pytest.mark.asyncio
    async def test_static_methods_use_custom_timeout(self):
        """Test that static methods respect custom timeout."""
        mock_response = []

        with aioresponses() as m:
            m.get("https://oekobox-online.eu/v3/shoplist.js.jsp", payload=mock_response)

            # Call with custom timeout - should not raise an error
            shops = await OekoboxClient.get_shop_info(timeout=60.0)
            assert isinstance(shops, list)
