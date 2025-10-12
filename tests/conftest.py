"""Test configuration and fixtures for pyoekoboxonline tests."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import httpx
import pytest

from pyoekoboxonline import OekoboxClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_client() -> OekoboxClient:
    """Create a sample OekoboxClient instance for testing."""
    return OekoboxClient(
        shop_id="test_shop", username="testuser", password="testpass", timeout=30.0
    )


@pytest.fixture
async def authenticated_client() -> AsyncGenerator[OekoboxClient, None]:
    """Create an authenticated OekoboxClient instance for testing.

    Note: This is a mock client that doesn't actually connect to the API.
    The session_id is set manually for testing purposes.
    """
    client = OekoboxClient(
        shop_id="test_shop", username="testuser", password="testpass"
    )
    # Mock authentication by setting session_id directly
    client.session_id = "test_session_12345"

    yield client

    # Cleanup
    await client.close()


@pytest.fixture
def sample_shop_data():
    """Sample shop data for testing."""
    return {
        "id": "test_shop",
        "name": "Test Organic Market",
        "latitude": 52.5200,
        "longitude": 13.4050,
        "delivery_lat": 52.5300,
        "delivery_lng": 13.4150,
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user_123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
    }


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "id": "item_123",
        "name": "Organic Apples",
        "description": "Fresh organic apples from local farm",
        "price": 3.99,
        "group_id": "fruits",
        "subgroup_id": "apples",
        "is_available": True,
        "image_url": "https://example.com/apple.jpg",
    }


@pytest.fixture
def sample_cart_item_data():
    """Sample cart item data for testing."""
    return {
        "item_id": "item_123",
        "quantity": 2.0,
        "unit_price": 3.99,
        "total_price": 7.98,
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "id": "order_123",
        "customer_id": "customer_456",
        "status": "confirmed",
        "order_date": "2023-10-15T10:00:00Z",
        "delivery_date": "2023-10-16T14:00:00Z",
        "total_amount": 15.99,
        "positions": [
            {
                "item_id": "item_123",
                "quantity": 2.0,
                "unit_price": 3.99,
                "total_price": 7.98,
            }
        ],
    }


@pytest.fixture
def mock_shop_list_js():
    """Mock JavaScript shop list content for testing."""
    return """[52.5200,13.4050,"Berlin Organic Market",52.5300,13.4150,"berlin_shop"]
[48.1351,11.5820,"Munich Bio Store",48.1400,11.5900,"munich_shop"]
[50.9375,6.9603,"Cologne Green Foods",-1,-1,"cologne_shop"]
[-1,-1,"Invalid Coordinates Shop",51.2277,6.7735,"invalid_shop"]"""


@pytest.fixture
def mock_httpx():
    """Mock httpx client for testing."""
    return AsyncMock(spec=httpx.AsyncClient)


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]
