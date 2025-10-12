"""Tests for Ökobox Online API data models."""

from datetime import datetime

from pyoekoboxonline.models import (
    Address,
    Box,
    CartItem,
    DDate,
    Delivery,
    DeliveryState,
    Group,
    Item,
    Navigation,
    Order,
    Position,
    Shop,
    SubGroup,
    Subscription,
    UserInfo,
    Voucher,
    XUnit,
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

    def test_shop_model_minimal(self):
        """Test Shop model with minimal required fields."""
        shop_data = {
            "id": "shop_456",
            "name": "Market",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        shop = Shop(**shop_data)
        assert shop.delivery_lat is None
        assert shop.delivery_lng is None

    def test_address_model_complete(self):
        """Test complete Address model."""
        address_data = {
            "street": "Muster Str. 123",
            "city": "Berlin",
            "postal_code": "10115",
            "country": "Germany",
            "latitude": 52.5200,
            "longitude": 13.4050,
        }
        address = Address(**address_data)
        assert address.street == "Muster Str. 123"
        assert address.city == "Berlin"
        assert address.postal_code == "10115"

    def test_address_model_empty(self):
        """Test Address model with all optional fields."""
        address = Address()
        assert address.street is None
        assert address.city is None
        assert address.postal_code is None

    def test_user_info_model(self):
        """Test UserInfo model."""
        user_data = {
            "id": "user_123",
            "username": "organic_lover",
            "email": "user@example.com",
            "first_name": "Anna",
            "last_name": "Müller",
            "is_active": True,
        }
        user = UserInfo(**user_data)
        assert user.username == "organic_lover"
        assert user.email == "user@example.com"
        assert user.is_active is True

    def test_item_model_complete(self):
        """Test complete Item model."""
        unit_data = {"id": "kg", "name": "Kilogram", "symbol": "kg"}
        unit = XUnit(**unit_data)

        item_data = {
            "id": "item_123",
            "name": "Organic Apples",
            "description": "Fresh organic apples from local farm",
            "price": 3.99,
            "unit": unit,
            "group_id": "fruits",
            "subgroup_id": "apples",
            "is_available": True,
            "image_url": "https://example.com/apple.jpg",
        }
        item = Item(**item_data)
        assert item.name == "Organic Apples"
        assert item.price == 3.99
        assert item.unit.symbol == "kg"
        assert item.is_available is True

    def test_cart_item_model(self):
        """Test CartItem model."""
        cart_item_data = {
            "item_id": "item_123",
            "quantity": 2.5,
            "unit_price": 3.99,
            "total_price": 9.98,
        }
        cart_item = CartItem(**cart_item_data)
        assert cart_item.item_id == "item_123"
        assert cart_item.quantity == 2.5
        assert cart_item.total_price == 9.98

    def test_order_model_with_positions(self):
        """Test Order model with positions."""
        position_data = {
            "id": "pos_1",
            "item_id": "item_123",
            "quantity": 2.0,
            "unit_price": 3.99,
            "total_price": 7.98,
        }
        position = Position(**position_data)

        order_data = {
            "id": "order_456",
            "customer_id": "customer_123",
            "status": "confirmed",
            "order_date": datetime(2024, 1, 15, 10, 30),
            "delivery_date": datetime(2024, 1, 16, 14, 0),
            "positions": [position],
            "total_amount": 7.98,
        }
        order = Order(**order_data)
        assert order.id == "order_456"
        assert len(order.positions) == 1
        assert order.positions[0].total_price == 7.98

    def test_delivery_state_enum(self):
        """Test DeliveryState enum."""
        assert DeliveryState.PLANNED == "planned"
        assert DeliveryState.IN_PROGRESS == "in_progress"
        assert DeliveryState.DELIVERED == "delivered"
        assert DeliveryState.FAILED == "failed"

    def test_delivery_model(self):
        """Test Delivery model."""
        delivery_data = {
            "id": "delivery_123",
            "order_id": "order_456",
            "status": DeliveryState.PLANNED,
            "planned_date": datetime(2024, 1, 16, 14, 0),
            "tracking_info": "TRACK123456",
        }
        delivery = Delivery(**delivery_data)
        assert delivery.status == DeliveryState.PLANNED
        assert delivery.tracking_info == "TRACK123456"

    def test_subscription_model(self):
        """Test Subscription model."""
        cart_item = CartItem(item_id="item_123", quantity=2.0)
        subscription_data = {
            "id": "sub_123",
            "customer_id": "customer_456",
            "items": [cart_item],
            "frequency": "weekly",
            "next_delivery": datetime(2024, 1, 22, 14, 0),
            "is_active": True,
            "is_paused": False,
        }
        subscription = Subscription(**subscription_data)
        assert subscription.frequency == "weekly"
        assert len(subscription.items) == 1
        assert subscription.is_active is True

    def test_voucher_model_with_dates(self):
        """Test Voucher model with validity dates."""
        voucher_data = {
            "id": "voucher_123",
            "code": "SAVE10",
            "name": "10% Discount",
            "discount_percentage": 10.0,
            "valid_from": datetime(2024, 1, 1),
            "valid_until": datetime(2024, 12, 31),
            "is_active": True,
        }
        voucher = Voucher(**voucher_data)
        assert voucher.code == "SAVE10"
        assert voucher.discount_percentage == 10.0
        assert voucher.is_active is True

    def test_navigation_model_with_children(self):
        """Test Navigation model with nested structure."""
        child_nav = Navigation(id="child_1", name="Apples", parent_id="fruits")
        parent_nav_data = {
            "id": "fruits",
            "name": "Fruits",
            "url": "/category/fruits",
            "children": [child_nav],
        }
        nav = Navigation(**parent_nav_data)
        assert nav.name == "Fruits"
        assert len(nav.children) == 1
        assert nav.children[0].name == "Apples"

    def test_group_and_subgroup_models(self):
        """Test Group and SubGroup models."""
        group_data = {
            "id": "fruits",
            "name": "Fresh Fruits",
            "description": "All kinds of fresh fruits",
        }
        group = Group(**group_data)

        subgroup_data = {
            "id": "apples",
            "name": "Apples",
            "description": "Different varieties of apples",
            "group_id": "fruits",
        }
        subgroup = SubGroup(**subgroup_data)

        assert group.name == "Fresh Fruits"
        assert subgroup.group_id == "fruits"

    def test_box_model(self):
        """Test Box model for packaging."""
        box_data = {
            "id": "box_small",
            "name": "Small Delivery Box",
            "capacity": 5.0,
            "is_returnable": True,
        }
        box = Box(**box_data)
        assert box.name == "Small Delivery Box"
        assert box.capacity == 5.0
        assert box.is_returnable is True

    def test_ddate_model(self):
        """Test DDate model for delivery dates."""
        ddate_data = {
            "date": datetime(2024, 1, 16, 14, 0),
            "is_available": True,
            "delivery_slots": ["09:00-12:00", "14:00-18:00"],
        }
        ddate = DDate(**ddate_data)
        assert ddate.is_available is True
        assert len(ddate.delivery_slots) == 2
        assert "09:00-12:00" in ddate.delivery_slots
