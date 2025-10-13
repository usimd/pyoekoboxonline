"""Tests for Ökobox Online API data models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from pyoekoboxonline.models import (
    Address,
    APIResponse,
    CartItem,
    CustomerInfo,
    DDate,
    Delivery,
    DeliveryState,
    Favourite,
    Group,
    Item,
    Order,
    Shop,
    SubGroup,
    Subscription,
    UserInfo,
)


class TestModels:
    """Test cases for Ökobox Online API Pydantic models."""

    def test_shop_model_valid(self):
        """Test valid Shop model creation."""
        shop_data = {
            "id": "shop_123",
            "name": "Organic Market Berlin",
            "latitude": 52.5200,
            "longitude": 13.4050,
            "delivery_lat": 52.5300,
            "delivery_lng": 13.4150,
        }
        shop = Shop(**shop_data)
        assert shop.id == "shop_123"
        assert shop.name == "Organic Market Berlin"
        assert shop.latitude == 52.5200
        assert shop.longitude == 13.4050
        assert shop.delivery_lat == 52.5300
        assert shop.delivery_lng == 13.4150

    def test_shop_model_minimal(self):
        """Test Shop model with minimal required fields."""
        shop_data = {
            "id": "shop_456",
            "name": "Market",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        shop = Shop(**shop_data)
        assert shop.id == "shop_456"
        assert shop.name == "Market"
        assert shop.latitude == 50.0
        assert shop.longitude == 10.0
        assert shop.delivery_lat is None
        assert shop.delivery_lng is None

    def test_address_model(self):
        """Test Address model creation."""
        address_data = {
            "street": "123 Main St",
            "city": "Berlin",
            "postal_code": "12345",
            "country": "Germany",
            "latitude": 52.5200,
            "longitude": 13.4050,
        }
        address = Address(**address_data)
        assert address.street == "123 Main St"
        assert address.city == "Berlin"
        assert address.postal_code == "12345"
        assert address.country == "Germany"
        assert address.latitude == 52.5200
        assert address.longitude == 13.4050

    def test_address_model_minimal(self):
        """Test Address model with minimal fields."""
        address = Address()
        assert address.street is None
        assert address.city is None
        assert address.postal_code is None
        assert address.country is None
        assert address.latitude is None
        assert address.longitude is None

    def test_user_info_model(self):
        """Test UserInfo model creation."""
        user_data = {
            "id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "pcgif_version": "1.0",
            "shop_version": "2.1",
        }
        user = UserInfo(**user_data)
        assert user.id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.pcgif_version == "1.0"
        assert user.shop_version == "2.1"

    def test_user_info_model_defaults(self):
        """Test UserInfo model with default values."""
        user = UserInfo()
        assert user.id is None
        assert user.username is None
        assert user.email is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.is_active is True
        assert user.pcgif_version is None
        assert user.shop_version is None

    def test_customer_info_model(self):
        """Test CustomerInfo model creation."""
        user_info = UserInfo(username="testuser", email="test@example.com")
        customer_data = {
            "id": "customer_123",
            "user_info": user_info,
        }
        customer = CustomerInfo(**customer_data)
        assert customer.id == "customer_123"
        assert customer.user_info.username == "testuser"
        assert customer.user_info.email == "test@example.com"
        assert customer.address is None

    def test_group_model(self):
        """Test Group model creation."""
        group_data = {
            "id": "group_1",
            "name": "Fruits",
            "info": "Fresh organic fruits",
            "count": 25,
        }
        group = Group(**group_data)
        assert group.id == "group_1"
        assert group.name == "Fruits"
        assert group.info == "Fresh organic fruits"
        assert group.count == 25

    def test_subgroup_model(self):
        """Test SubGroup model creation."""
        subgroup_data = {
            "id": "subgroup_1",
            "name": "Apples",
            "parent_id": "group_1",
            "count": 5,
        }
        subgroup = SubGroup(**subgroup_data)
        assert subgroup.id == "subgroup_1"
        assert subgroup.name == "Apples"
        assert subgroup.parent_id == "group_1"
        assert subgroup.count == 5

    def test_item_model(self):
        """Test Item model creation."""
        item_data = {
            "id": "item_123",
            "name": "Organic Apples",
            "price": 3.99,
            "description": "Fresh organic apples",
            "group_id": "group_1",
            "subgroup_id": "subgroup_1",
            "unit": "kg",
            "is_available": True,
            "image_url": "https://example.com/apple.jpg",
        }
        item = Item(**item_data)
        assert item.id == "item_123"
        assert item.name == "Organic Apples"
        assert item.price == 3.99
        assert item.description == "Fresh organic apples"
        assert item.group_id == "group_1"
        assert item.subgroup_id == "subgroup_1"
        assert item.unit == "kg"
        assert item.is_available is True
        assert item.image_url == "https://example.com/apple.jpg"

    def test_cart_item_model(self):
        """Test CartItem model creation."""
        cart_item_data = {
            "item_id": "item_123",
            "quantity": 2.5,
            "unit": "kg",
            "price": 3.99,
            "unit_price": 3.99,
            "total_price": 9.98,
            "note": "Extra ripe please",
        }
        cart_item = CartItem(**cart_item_data)
        assert cart_item.item_id == "item_123"
        assert cart_item.quantity == 2.5
        assert cart_item.unit == "kg"
        assert cart_item.price == 3.99
        assert cart_item.unit_price == 3.99
        assert cart_item.total_price == 9.98
        assert cart_item.note == "Extra ripe please"

    def test_ddate_model(self):
        """Test DDate model creation."""
        delivery_date = datetime(2023, 12, 25, 10, 0, 0)
        ddate_data = {
            "date": delivery_date,
            "is_available": True,
            "delivery_slots": ["10:00-12:00", "14:00-16:00"],
        }
        ddate = DDate(**ddate_data)
        assert ddate.date == delivery_date
        assert ddate.is_available is True
        assert ddate.delivery_slots == ["10:00-12:00", "14:00-16:00"]

    def test_subscription_model(self):
        """Test Subscription model creation."""
        next_delivery = date(2023, 12, 25)
        subscription_data = {
            "id": "sub_123",
            "customer_id": "customer_123",
            "frequency": "weekly",
            "is_active": True,
            "next_delivery": next_delivery,
        }
        subscription = Subscription(**subscription_data)
        assert subscription.id == "sub_123"
        assert subscription.customer_id == "customer_123"
        assert subscription.frequency == "weekly"
        assert subscription.is_active is True
        assert subscription.next_delivery == next_delivery

    def test_favourite_model(self):
        """Test Favourite model creation."""
        favourite_data = {
            "customer_id": "customer_123",
            "item_id": "item_123",
        }
        favourite = Favourite(**favourite_data)
        assert favourite.customer_id == "customer_123"
        assert favourite.item_id == "item_123"

    def test_order_model(self):
        """Test Order model creation."""
        delivery_date = date(2023, 12, 25)
        cart_item = CartItem(item_id="item_123", quantity=2.0)
        order_data = {
            "id": "order_123",
            "customer_id": "customer_123",
            "delivery_date": delivery_date,
            "status": "confirmed",
            "total": 19.98,
            "items": [cart_item],
        }
        order = Order(**order_data)
        assert order.id == "order_123"
        assert order.customer_id == "customer_123"
        assert order.delivery_date == delivery_date
        assert order.status == "confirmed"
        assert order.total == 19.98
        assert len(order.items) == 1
        assert order.items[0].item_id == "item_123"

    def test_delivery_state_enum(self):
        """Test DeliveryState enum values."""
        assert DeliveryState.PENDING == "pending"
        assert DeliveryState.CONFIRMED == "confirmed"
        assert DeliveryState.IN_TRANSIT == "in_transit"
        assert DeliveryState.DELIVERED == "delivered"
        assert DeliveryState.CANCELLED == "cancelled"

    def test_delivery_model(self):
        """Test Delivery model creation."""
        delivery_date = date(2023, 12, 25)
        address = Address(street="123 Main St", city="Berlin")
        delivery_data = {
            "id": "delivery_123",
            "order_id": "order_123",
            "delivery_date": delivery_date,
            "state": DeliveryState.CONFIRMED,
            "address": address,
        }
        delivery = Delivery(**delivery_data)
        assert delivery.id == "delivery_123"
        assert delivery.order_id == "order_123"
        assert delivery.delivery_date == delivery_date
        assert delivery.state == DeliveryState.CONFIRMED
        assert delivery.address.street == "123 Main St"

    def test_api_response_model(self):
        """Test APIResponse model creation."""
        response_data = {
            "action": "login",
            "result": "ok",
            "data": {"user_id": "123"},
        }
        response = APIResponse(**response_data)
        assert response.action == "login"
        assert response.result == "ok"
        assert response.data == {"user_id": "123"}

    def test_model_validation_errors(self):
        """Test that models raise validation errors for invalid data."""
        # Test missing required fields
        with pytest.raises(ValidationError):
            Shop(name="Test Shop")  # Missing id, latitude, longitude

        with pytest.raises(ValidationError):
            Group(name="Test Group")  # Missing id

        with pytest.raises(ValidationError):
            CartItem()  # Missing item_id

    def test_model_serialization(self):
        """Test that models can be serialized to dict."""
        shop = Shop(id="test_shop", name="Test Shop", latitude=52.0, longitude=13.0)
        shop_dict = shop.model_dump()
        assert shop_dict["id"] == "test_shop"
        assert shop_dict["name"] == "Test Shop"
        assert shop_dict["latitude"] == 52.0
        assert shop_dict["longitude"] == 13.0
        assert shop_dict["delivery_lat"] is None
        assert shop_dict["delivery_lng"] is None
