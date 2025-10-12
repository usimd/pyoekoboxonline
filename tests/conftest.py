"""Pytest configuration and fixtures for Ökobox Online API tests."""

from unittest.mock import AsyncMock

import httpx
import pytest


@pytest.fixture
def base_url():
    """Base URL for test API."""
    return "https://api.test.oekobox.com"


@pytest.fixture
def shop_id():
    """Test shop ID."""
    return "test_shop_123"


@pytest.fixture
def username():
    """Test username."""
    return "testuser"


@pytest.fixture
def password():
    """Test password."""
    return "testpass123"


@pytest.fixture
def sample_shop_data():
    """Sample shop data for testing."""
    return {
        "id": "shop_123",
        "name": "Berlin Organic Market",
        "latitude": 52.5200,
        "longitude": 13.4050,
        "delivery_lat": 52.5300,
        "delivery_lng": 13.4150,
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user_456",
        "username": "organic_fan",
        "email": "user@example.com",
        "first_name": "Max",
        "last_name": "Mustermann",
        "is_active": True,
    }


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "id": "item_789",
        "name": "Organic Tomatoes",
        "description": "Fresh organic tomatoes from local farm",
        "price": 4.50,
        "group_id": "vegetables",
        "subgroup_id": "tomatoes",
        "is_available": True,
        "image_url": "https://example.com/tomato.jpg",
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "id": "order_123",
        "customer_id": "customer_456",
        "status": "confirmed",
        "order_date": "2024-01-15T10:30:00Z",
        "delivery_date": "2024-01-16T14:00:00Z",
        "total_amount": 23.45,
        "positions": [
            {
                "id": "pos_1",
                "item_id": "item_789",
                "quantity": 2.0,
                "unit_price": 4.50,
                "total_price": 9.00,
            }
        ],
    }


@pytest.fixture
def mock_httpx():
    """Mock httpx client for testing."""
    return AsyncMock(spec=httpx.AsyncClient)
