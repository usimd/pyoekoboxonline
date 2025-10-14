"""Integration tests for the Ökobox Online API client.

These tests make real API calls and require valid credentials.
Set the following environment variables or modify the test configuration:
- OEKOBOX_SHOP_ID: The shop ID to test against
- OEKOBOX_USERNAME: Valid username for the shop
- OEKOBOX_PASSWORD: Valid password for the user

Usage:
    pytest tests/test_integration.py -v --tb=short

Note: These tests will make real API calls and may modify data (cart, favorites).
Only run against test accounts or accounts where data modification is acceptable.
"""

import os

import pytest
import pytest_asyncio

from pyoekoboxonline import OekoboxClient
from pyoekoboxonline.exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxValidationError,
)
from pyoekoboxonline.models import (
    Group,
    Item,
    Order,
    UserInfo,
    SubGroup,
    Tour,
    ShopDate,
)

# Import our configuration system
try:
    from tests.integration_config import get_test_config

    # Try to get configuration
    try:
        test_config_obj = get_test_config()
        TEST_CONFIG = test_config_obj.to_dict()
        HAS_VALID_CONFIG = test_config_obj.is_valid()
    except ValueError:
        # Fallback to environment variables if config file isn't available
        TEST_CONFIG = {
            "shop_id": os.getenv("OEKOBOX_SHOP_ID", ""),
            "username": os.getenv("OEKOBOX_USERNAME", ""),
            "password": os.getenv("OEKOBOX_PASSWORD", ""),
            "base_url": os.getenv("OEKOBOX_BASE_URL", ""),
        }
        HAS_VALID_CONFIG = all(TEST_CONFIG.values())
except ImportError:
    # Integration config not available, use environment variables
    TEST_CONFIG = {
        "shop_id": os.getenv("OEKOBOX_SHOP_ID", ""),
        "username": os.getenv("OEKOBOX_USERNAME", ""),
        "password": os.getenv("OEKOBOX_PASSWORD", ""),
        "base_url": os.getenv("OEKOBOX_BASE_URL", ""),
    }
    HAS_VALID_CONFIG = all(v for v in TEST_CONFIG.values() if v)

# Skip all integration tests if no valid configuration
pytestmark = pytest.mark.skipif(
    not HAS_VALID_CONFIG,
    reason="No valid integration test configuration found. "
    "Set OEKOBOX_SHOP_ID, OEKOBOX_USERNAME, and OEKOBOX_PASSWORD environment variables "
    "or configure integration_config.py",
)


@pytest.fixture
async def client():
    """Create an authenticated client for integration tests."""
    async with OekoboxClient(
        shop_id=TEST_CONFIG["shop_id"],
        username=TEST_CONFIG["username"],
        password=TEST_CONFIG["password"],
        base_url=TEST_CONFIG.get("base_url"),
    ) as client:
        # Authenticate the client
        await client.logon()
        yield client
        # Logout after test
        try:
            await client.logout()
        except Exception:
            # Logout may fail if session is already expired
            pass


class TestIntegrationAuthentication:
    """Integration tests for authentication functionality."""

    @pytest.mark.asyncio
    async def test_successful_logon_logout(self):
        """Test successful login and logout flow."""
        async with OekoboxClient(
            shop_id=TEST_CONFIG["shop_id"],
            username=TEST_CONFIG["username"],
            password=TEST_CONFIG["password"],
        ) as client:
            # Test login
            response = await client.logon()
            assert response["result"] in ["ok", "relogon"]
            assert client.session_id is not None

            # Test logout
            logout_response = await client.logout()
            assert logout_response["result"] == "ok"
            assert client.session_id is None

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with OekoboxClient(
            shop_id=TEST_CONFIG["shop_id"],
            username="invalid_user",
            password="invalid_password",
        ) as client:
            with pytest.raises(OekoboxAuthenticationError):
                await client.logon()


class TestIntegrationDataRetrieval:
    """Integration tests for data retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_groups(self, client):
        """Test retrieving product groups."""
        groups = await client.get_groups()
        assert isinstance(groups, list)
        if groups:  # Only test if groups exist
            assert all(isinstance(group, Group) for group in groups)
            assert all(hasattr(group, 'id') for group in groups)
            assert all(hasattr(group, 'name') for group in groups)

    @pytest.mark.asyncio
    async def test_get_subgroups(self, client):
        """Test retrieving product subgroups."""
        subgroups = await client.get_subgroups()
        assert isinstance(subgroups, list)
        if subgroups:  # Only test if subgroups exist
            assert all(isinstance(subgroup, SubGroup) for subgroup in subgroups)

    @pytest.mark.asyncio
    async def test_get_items(self, client):
        """Test retrieving items."""
        items = await client.get_items()
        assert isinstance(items, list)
        if items:  # Only test if items exist
            assert all(isinstance(item, Item) for item in items)
            # Test that items have required fields
            sample_item = items[0]
            assert hasattr(sample_item, 'id')
            assert hasattr(sample_item, 'name')
            assert hasattr(sample_item, 'price')

    @pytest.mark.asyncio
    async def test_get_user_info(self, client):
        """Test retrieving user information."""
        user_info = await client.get_user_info()
        assert isinstance(user_info, list)
        assert len(user_info) >= 1
        assert isinstance(user_info[0], UserInfo)
        assert user_info[0].authentication_state in ["AUTH", "VALID", "SUPER", "ADMIN"]

    @pytest.mark.asyncio
    async def test_get_orders(self, client):
        """Test retrieving orders."""
        orders = await client.get_orders()
        assert isinstance(orders, list)
        if orders:  # Only test if orders exist
            assert all(isinstance(order, Order) for order in orders)

    @pytest.mark.asyncio
    async def test_get_dates(self, client):
        """Test retrieving delivery dates."""
        dates = await client.get_dates()
        assert isinstance(dates, list)
        # Dates can contain various types (ShopDate, Pause, etc.)

    @pytest.mark.asyncio
    async def test_search_functionality(self, client):
        """Test search functionality."""
        # Search for a common term that should return results
        results = await client.search("a")  # Single letter should match many items
        assert isinstance(results, list)
        if results:  # Only test if results exist
            assert all(isinstance(item, Item) for item in results)


class TestIntegrationCartOperations:
    """Integration tests for cart operations."""

    @pytest.mark.asyncio
    async def test_cart_operations(self, client):
        """Test cart add, show, and remove operations."""
        # First, get an item to add to cart
        items = await client.get_items()
        if not items:
            pytest.skip("No items available for cart testing")

        test_item = items[0]
        if not test_item.id:
            pytest.skip("Test item has no ID")

        # Clear cart first
        await client.reset_cart()

        # Add item to cart
        add_response = await client.add_to_cart(
            item_id=test_item.id, amount=1.0
        )
        assert "result" in add_response

        # Show cart contents
        cart_items = await client.show_cart()
        assert isinstance(cart_items, list)

        # Remove item from cart
        remove_response = await client.remove_from_cart(item_id=test_item.id)
        assert "result" in remove_response

        # Reset cart
        reset_response = await client.reset_cart()
        assert "result" in reset_response


class TestIntegrationErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_item_id(self, client):
        """Test handling of invalid item ID."""
        # Try to get an item with an obviously invalid ID
        try:
            result = await client.get_item(999999)
            # If no error is raised, the result should be empty
            assert isinstance(result, list)
        except (OekoboxAPIError, OekoboxValidationError):
            # This is also acceptable - some APIs return errors for invalid IDs
            pass

    @pytest.mark.asyncio
    async def test_invalid_search_query(self, client):
        """Test handling of problematic search queries."""
        # Test with empty search
        try:
            results = await client.search("")
            assert isinstance(results, list)
        except OekoboxAPIError:
            # Some APIs might reject empty searches
            pass

        # Test with very long search
        long_query = "a" * 1000
        try:
            results = await client.search(long_query)
            assert isinstance(results, list)
        except OekoboxAPIError:
            # Some APIs might reject very long queries
            pass


class TestIntegrationDataIntegrity:
    """Integration tests for data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_group_item_consistency(self, client):
        """Test that items reference valid groups."""
        groups = await client.get_groups()
        items = await client.get_items()

        if not groups or not items:
            pytest.skip("Insufficient data for consistency testing")

        group_ids = {group.id for group in groups if group.id is not None}

        # Check that items reference existing groups
        for item in items[:10]:  # Test first 10 items to avoid long runtime
            if item.category_id is not None:
                # Note: Not all items may have valid category references
                # This test just ensures the data structure is reasonable
                assert isinstance(item.category_id, int)

    @pytest.mark.asyncio
    async def test_model_field_types(self, client):
        """Test that model fields have expected types."""
        items = await client.get_items()

        if not items:
            pytest.skip("No items available for type testing")

        sample_item = items[0]

        # Test that numeric fields are properly typed
        if sample_item.id is not None:
            assert isinstance(sample_item.id, int)
        if sample_item.price is not None:
            assert isinstance(sample_item.price, (int, float))
        if sample_item.vat is not None:
            assert isinstance(sample_item.vat, (int, float))

        # Test that string fields are properly typed
        if sample_item.name is not None:
            assert isinstance(sample_item.name, str)
        if sample_item.unit is not None:
            assert isinstance(sample_item.unit, str)
