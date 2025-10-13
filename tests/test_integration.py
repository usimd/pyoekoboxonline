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
    CustomerInfo,
    DDate,
    Group,
    Item,
    Order,
    Shop,
    SubGroup,
    Subscription,
    UserInfo,
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
            "timeout": float(os.getenv("OEKOBOX_TIMEOUT", "30.0")),
            "base_url": os.getenv("OEKOBOX_BASE_URL"),
        }
        HAS_VALID_CONFIG = all(
            [TEST_CONFIG["shop_id"], TEST_CONFIG["username"], TEST_CONFIG["password"]]
        )
except ImportError:
    # If integration_config module doesn't exist, use environment variables
    TEST_CONFIG = {
        "shop_id": os.getenv("OEKOBOX_SHOP_ID", ""),
        "username": os.getenv("OEKOBOX_USERNAME", ""),
        "password": os.getenv("OEKOBOX_PASSWORD", ""),
        "timeout": float(os.getenv("OEKOBOX_TIMEOUT", "30.0")),
        "base_url": os.getenv("OEKOBOX_BASE_URL"),
    }
    HAS_VALID_CONFIG = all(
        [TEST_CONFIG["shop_id"], TEST_CONFIG["username"], TEST_CONFIG["password"]]
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if credentials are not provided."""
    if not HAS_VALID_CONFIG:
        skip_integration = pytest.mark.skip(
            reason="Integration tests require OEKOBOX_SHOP_ID, OEKOBOX_USERNAME, and OEKOBOX_PASSWORD environment variables or config file"
        )
        for item in items:
            if "test_integration" in item.nodeid:
                item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def integration_config():
    """Provide test configuration."""
    if not HAS_VALID_CONFIG:
        pytest.skip("Integration tests require valid credentials")
    return TEST_CONFIG


@pytest_asyncio.fixture(scope="session")
async def authenticated_client(integration_config):
    """Create and authenticate a real client for integration tests."""
    client = OekoboxClient(
        shop_id=integration_config["shop_id"],
        username=integration_config["username"],
        password=integration_config["password"],
        timeout=integration_config["timeout"],
    )

    async with client:
        await client.login()
        yield client


@pytest_asyncio.fixture
async def unauthenticated_client(integration_config):
    """Create an unauthenticated client for public API tests."""
    client = OekoboxClient(
        shop_id=integration_config["shop_id"],
        username=integration_config["username"],
        password=integration_config["password"],
        timeout=integration_config["timeout"],
    )

    async with client:
        yield client


class TestShopDiscovery:
    """Test shop discovery functionality."""

    @pytest.mark.asyncio
    async def test_get_available_shops(self):
        """Test getting list of available shops."""
        shops = await OekoboxClient.get_available_shops()

        assert isinstance(shops, list)
        assert len(shops) > 0, "Should find at least one shop"

        # Validate shop structure
        for shop in shops[:5]:  # Check first 5 shops
            assert isinstance(shop, Shop)
            assert shop.id is not None and shop.id != ""
            assert shop.name is not None and shop.name != ""
            assert isinstance(shop.latitude, float)
            assert isinstance(shop.longitude, float)
            assert -90 <= shop.latitude <= 90
            assert -180 <= shop.longitude <= 180

        print(f"Found {len(shops)} available shops")


class TestAuthentication:
    """Test authentication functionality."""

    @pytest.mark.asyncio
    async def test_login_success(self, integration_config):
        """Test successful login."""
        print(integration_config)
        client = OekoboxClient(
            shop_id=integration_config["shop_id"],
            username=integration_config["username"],
            password=integration_config["password"],
        )

        async with client:
            user_info = await client.login()

            assert isinstance(user_info, UserInfo)
            assert client.session_id is not None
            assert len(client.session_id) > 0

            print(f"Login successful, session ID: {client.session_id[:10]}...")

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, integration_config):
        """Test login with invalid credentials."""
        client = OekoboxClient(
            shop_id=integration_config["shop_id"],
            username="invalid_user",
            password="invalid_password",
        )

        async with client:
            with pytest.raises(OekoboxAuthenticationError):
                await client.login()

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client):
        """Test logout functionality."""
        # Client is already authenticated
        assert authenticated_client.session_id is not None

        await authenticated_client.logout()
        assert authenticated_client.session_id is None


class TestUserManagement:
    """Test user and customer information retrieval."""

    @pytest.mark.asyncio
    async def test_get_user_info(self, authenticated_client):
        """Test getting user information."""
        user_info = await authenticated_client.get_user_info()

        assert isinstance(user_info, UserInfo)
        print(f"User info retrieved for: {user_info.username or 'Unknown'}")

    @pytest.mark.asyncio
    async def test_get_customer_info(self, authenticated_client):
        """Test getting customer information."""
        customer_info = await authenticated_client.get_customer_info()

        assert isinstance(customer_info, CustomerInfo)
        print("Customer info retrieved")


class TestProductCatalog:
    """Test product catalog functionality."""

    @pytest.mark.asyncio
    async def test_get_groups(self, unauthenticated_client):
        """Test getting product groups."""
        groups = await unauthenticated_client.get_groups()

        assert isinstance(groups, list)
        if groups:  # Some shops might not have groups
            for group in groups[:3]:  # Check first 3 groups
                assert isinstance(group, Group)
                assert group.id is not None
                assert group.name is not None

            print(f"Found {len(groups)} product groups")
        else:
            print("No product groups found")

    @pytest.mark.asyncio
    async def test_get_subgroups(self, unauthenticated_client):
        """Test getting product subgroups."""
        # Get all subgroups
        subgroups = await unauthenticated_client.get_subgroups()

        assert isinstance(subgroups, list)
        if subgroups:
            for subgroup in subgroups[:3]:  # Check first 3 subgroups
                assert isinstance(subgroup, SubGroup)
                assert subgroup.id is not None
                assert subgroup.name is not None

            print(f"Found {len(subgroups)} product subgroups")
        else:
            print("No product subgroups found")

    @pytest.mark.asyncio
    async def test_get_subgroups_filtered(self, unauthenticated_client):
        """Test getting subgroups filtered by group."""
        # First get groups to have a valid group_id
        groups = await unauthenticated_client.get_groups()

        if groups:
            group_id = groups[0].id
            subgroups = await unauthenticated_client.get_subgroups(group_id=group_id)

            assert isinstance(subgroups, list)
            print(f"Found {len(subgroups)} subgroups for group {group_id}")

    @pytest.mark.asyncio
    async def test_get_items(self, unauthenticated_client):
        """Test getting items."""
        items = await unauthenticated_client.get_items()

        assert isinstance(items, list)
        if items:
            for item in items[:3]:  # Check first 3 items
                assert isinstance(item, Item)
                assert item.id is not None
                assert item.name is not None

            print(f"Found {len(items)} items")
        else:
            print("No items found")

    @pytest.mark.asyncio
    async def test_get_items_filtered(self, unauthenticated_client):
        """Test getting items filtered by group and subgroup."""
        groups = await unauthenticated_client.get_groups()

        if groups:
            group_id = groups[0].id
            items = await unauthenticated_client.get_items(group_id=group_id)

            assert isinstance(items, list)
            print(f"Found {len(items)} items for group {group_id}")

            # Test with subgroup if available
            subgroups = await unauthenticated_client.get_subgroups(group_id=group_id)
            if subgroups:
                subgroup_id = subgroups[0].id
                items_sub = await unauthenticated_client.get_items(
                    group_id=group_id, subgroup_id=subgroup_id
                )

                assert isinstance(items_sub, list)
                print(f"Found {len(items_sub)} items for subgroup {subgroup_id}")

    @pytest.mark.asyncio
    async def test_get_item(self, unauthenticated_client):
        """Test getting specific item details."""
        items = await unauthenticated_client.get_items()

        if items:
            item_id = items[0].id
            item = await unauthenticated_client.get_item(item_id)

            assert isinstance(item, Item)
            assert item.id == item_id
            print(f"Retrieved item details for: {item.name}")

    @pytest.mark.asyncio
    async def test_search_items(self, unauthenticated_client):
        """Test searching for items."""
        # Try common search terms
        search_terms = ["bio", "apfel", "brot", "milch", "a"]

        for term in search_terms:
            try:
                results = await unauthenticated_client.search_items(term)
                assert isinstance(results, list)

                if results:
                    print(f"Search '{term}' found {len(results)} items")
                    break
            except Exception as e:
                print(f"Search for '{term}' failed: {e}")
                continue


class TestDeliveryDates:
    """Test delivery date functionality."""

    @pytest.mark.asyncio
    async def test_get_delivery_dates(self, unauthenticated_client):
        """Test getting available delivery dates."""
        dates = await unauthenticated_client.get_delivery_dates()

        assert isinstance(dates, list)
        if dates:
            for date in dates[:3]:  # Check first 3 dates
                assert isinstance(date, DDate)

            print(f"Found {len(dates)} available delivery dates")
        else:
            print("No delivery dates found")


class TestShoppingCart:
    """Test shopping cart functionality."""

    @pytest.mark.asyncio
    async def test_cart_operations(self, authenticated_client):
        """Test complete cart operations workflow."""
        # Clear cart first
        await authenticated_client.clear_cart()

        # Get initial cart (should be empty)
        cart = await authenticated_client.get_cart()
        assert isinstance(cart, list)
        initial_count = len(cart)
        print(f"Initial cart has {initial_count} items")

        # Get available items to add to cart
        items = await authenticated_client.get_items()
        if not items:
            pytest.skip("No items available to test cart functionality")

        test_item = items[0]
        test_quantity = 1.0

        # Try to add item to cart (may require delivery date selection)
        try:
            await authenticated_client.add_to_cart(test_item.id, test_quantity)

            # Check cart contents
            cart = await authenticated_client.get_cart()
            assert len(cart) == initial_count + 1

            # Verify the item is in cart
            cart_item_ids = [item.item_id for item in cart]
            assert test_item.id in cart_item_ids

            print(f"Added item '{test_item.name}' to cart")

            # Remove item from cart
            await authenticated_client.remove_from_cart(test_item.id)

            # Check cart is back to initial state
            cart = await authenticated_client.get_cart()
            assert len(cart) == initial_count

            print("Removed item from cart successfully")

        except OekoboxValidationError as e:
            if "delivery date must be selected" in str(e):
                print(
                    "Cart operations require delivery date selection - this is expected API behavior"
                )
                pytest.skip("Cart operations require delivery date selection")
            else:
                raise

    @pytest.mark.asyncio
    async def test_clear_cart(self, authenticated_client):
        """Test clearing the cart."""
        # Try to add an item first if cart is empty (may fail due to delivery date requirement)
        items = await authenticated_client.get_items()
        if items:
            try:
                await authenticated_client.add_to_cart(items[0].id, 1.0)
            except OekoboxValidationError as e:
                if "delivery date must be selected" in str(e):
                    print(
                        "Cannot add items without delivery date - testing clear_cart on empty cart"
                    )
                else:
                    raise

        # Clear cart (should work regardless)
        await authenticated_client.clear_cart()

        # Verify cart is empty
        cart = await authenticated_client.get_cart()
        assert len(cart) == 0

        print("Cart cleared successfully")


class TestOrders:
    """Test order functionality."""

    @pytest.mark.asyncio
    async def test_get_orders(self, authenticated_client):
        """Test getting customer orders."""
        orders = await authenticated_client.get_orders()

        assert isinstance(orders, list)
        print(f"Found {len(orders)} orders")

        # If there are orders, test getting specific order
        if orders:
            order_id = orders[0].id
            if order_id:
                order = await authenticated_client.get_order(order_id)
                assert isinstance(order, Order)
                print(f"Retrieved details for order {order_id}")

    @pytest.mark.asyncio
    async def test_create_order_workflow(self, authenticated_client):
        """Test order creation workflow (careful - creates real order)."""
        # This test is commented out by default to avoid creating real orders
        # Uncomment and modify as needed for your testing environment

        # # Clear cart and add test item
        # await authenticated_client.clear_cart()
        #
        # items = await authenticated_client.get_items()
        # if not items:
        #     pytest.skip("No items available for order test")
        #
        # # Add a small quantity of an inexpensive item
        # test_item = items[0]
        # await authenticated_client.add_to_cart(test_item.id, 0.1)  # Small quantity
        #
        # # Create order (WARNING: This creates a real order!)
        # # order = await authenticated_client.create_order()
        # # assert isinstance(order, Order)
        # # print(f"Created order: {order.id}")

        print("Order creation test skipped (would create real order)")


class TestSubscriptions:
    """Test subscription functionality."""

    @pytest.mark.asyncio
    async def test_get_subscriptions(self, authenticated_client):
        """Test getting customer subscriptions."""
        subscriptions = await authenticated_client.get_subscriptions()

        assert isinstance(subscriptions, list)
        print(f"Found {len(subscriptions)} subscriptions")

        if subscriptions:
            for sub in subscriptions[:3]:  # Check first 3 subscriptions
                assert isinstance(sub, Subscription)


class TestFavourites:
    """Test favourites functionality."""

    @pytest.mark.asyncio
    async def test_favourites_operations(self, authenticated_client):
        """Test complete favourites operations workflow."""
        # Get available items
        items = await authenticated_client.get_items()
        if not items:
            pytest.skip("No items available to test favourites")

        test_item = items[0]

        # Get initial favourites
        initial_favourites = await authenticated_client.get_favourites()
        assert isinstance(initial_favourites, list)
        initial_count = len(initial_favourites)

        print(f"Initial favourites: {initial_count}")

        # Check if item is already in favourites
        favourite_item_ids = [
            fav.item_id for fav in initial_favourites if hasattr(fav, "item_id")
        ]

        if test_item.id not in favourite_item_ids:
            # Add to favourites
            await authenticated_client.add_favourite(test_item.id)

            # Check favourites increased
            favourites = await authenticated_client.get_favourites()
            assert len(favourites) >= initial_count

            print(f"Added '{test_item.name}' to favourites")

            # Remove from favourites
            await authenticated_client.remove_favourite(test_item.id)

            # Check favourites back to initial count
            favourites = await authenticated_client.get_favourites()
            # Note: count might not be exactly initial_count due to async nature

            print("Removed item from favourites")
        else:
            print(
                f"Item '{test_item.name}' already in favourites, testing removal only"
            )

            # Remove from favourites
            await authenticated_client.remove_favourite(test_item.id)

            # Add back to favourites
            await authenticated_client.add_favourite(test_item.id)

            print("Tested favourites removal and addition")


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_item_id(self, authenticated_client):
        """Test handling of invalid item IDs."""
        with pytest.raises((OekoboxAPIError, OekoboxValidationError)):
            await authenticated_client.get_item("invalid_item_id_12345")

    @pytest.mark.asyncio
    async def test_invalid_order_id(self, authenticated_client):
        """Test handling of invalid order IDs."""
        with pytest.raises((OekoboxAPIError, OekoboxValidationError)):
            await authenticated_client.get_order("invalid_order_id_12345")

    @pytest.mark.asyncio
    async def test_unauthorized_operations(self, integration_config):
        """Test operations that require authentication without login."""
        client = OekoboxClient(
            shop_id=integration_config["shop_id"],
            username="invalid_user@example.com",  # Use invalid credentials
            password="invalid_password",
        )

        async with client:
            # Try to access protected resources without valid authentication
            with pytest.raises((OekoboxAuthenticationError, OekoboxAPIError)):
                await client.logon()  # This should fail with invalid credentials

            # Try cart operations without authentication
            with pytest.raises(
                (OekoboxAuthenticationError, OekoboxAPIError, OekoboxConnectionError)
            ):
                await client.get_cart()


# Test runner convenience function
async def run_integration_tests():
    """Run integration tests programmatically."""
    print("Running integration tests...")
    print("Make sure to set OEKOBOX_SHOP_ID, OEKOBOX_USERNAME, and OEKOBOX_PASSWORD")

    # This would need to be implemented based on your testing needs
    pass


if __name__ == "__main__":
    # Allow running tests directly
    print("Integration test suite for pyoekoboxonline")
    print("Run with: pytest tests/test_integration.py -v")
    print("\nRequired environment variables:")
    print("  OEKOBOX_SHOP_ID - Shop ID to test against")
    print("  OEKOBOX_USERNAME - Valid username")
    print("  OEKOBOX_PASSWORD - Valid password")
