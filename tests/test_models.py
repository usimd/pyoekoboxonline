"""Tests for Ökobox Online API data models."""

from datetime import datetime

from pyoekoboxonline.models import (
    Address,
    APIResponse,
    Article,
    Box,
    CartItem,
    CustomerInfo,
    DDate,
    Delivery,
    DeliveryState,
    Discount,
    Favourite,
    Group,
    Item,
    Navigation,
    Order,
    Position,
    Shop,
    SubGroup,
    Subscription,
    Tour,
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
        }
        user = UserInfo(**user_data)
        assert user.id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True

    def test_user_info_model_minimal(self):
        """Test UserInfo model with minimal fields."""
        user = UserInfo()
        assert user.id is None
        assert user.username is None
        assert user.email is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.is_active is True  # Default value

    def test_customer_info_model(self):
        """Test CustomerInfo model creation."""
        customer_data = {
            "id": "customer_123",
            "user_info": {
                "id": "user_123",
                "username": "testuser",
                "email": "test@example.com",
            },
            "delivery_address": {"street": "123 Main St", "city": "Berlin"},
            "billing_address": {"street": "456 Elm St", "city": "Munich"},
        }
        customer = CustomerInfo(**customer_data)
        assert customer.id == "customer_123"
        assert isinstance(customer.user_info, UserInfo)
        assert customer.user_info.username == "testuser"
        assert isinstance(customer.delivery_address, Address)
        assert customer.delivery_address.street == "123 Main St"
        assert isinstance(customer.billing_address, Address)
        assert customer.billing_address.street == "456 Elm St"

    def test_xunit_model(self):
        """Test XUnit model creation."""
        unit_data = {"id": "kg", "name": "Kilogram", "symbol": "kg"}
        unit = XUnit(**unit_data)
        assert unit.id == "kg"
        assert unit.name == "Kilogram"
        assert unit.symbol == "kg"

    def test_group_model(self):
        """Test Group model creation."""
        group_data = {
            "id": "fruits",
            "name": "Fresh Fruits",
            "description": "Organic fresh fruits",
            "parent_id": "produce",
        }
        group = Group(**group_data)
        assert group.id == "fruits"
        assert group.name == "Fresh Fruits"
        assert group.description == "Organic fresh fruits"
        assert group.parent_id == "produce"

    def test_group_model_minimal(self):
        """Test Group model with required fields only."""
        group_data = {"id": "vegetables", "name": "Vegetables"}
        group = Group(**group_data)
        assert group.id == "vegetables"
        assert group.name == "Vegetables"
        assert group.description is None
        assert group.parent_id is None

    def test_subgroup_model(self):
        """Test SubGroup model creation."""
        subgroup_data = {
            "id": "apples",
            "name": "Apples",
            "description": "Various apple varieties",
            "group_id": "fruits",
        }
        subgroup = SubGroup(**subgroup_data)
        assert subgroup.id == "apples"
        assert subgroup.name == "Apples"
        assert subgroup.description == "Various apple varieties"
        assert subgroup.group_id == "fruits"

    def test_item_model(self):
        """Test Item model creation."""
        item_data = {
            "id": "apple_001",
            "name": "Organic Apples",
            "description": "Fresh organic apples from local farm",
            "price": 3.99,
            "unit": {"id": "kg", "name": "Kilogram", "symbol": "kg"},
            "group_id": "fruits",
            "subgroup_id": "apples",
            "is_available": True,
            "image_url": "https://example.com/apple.jpg",
        }
        item = Item(**item_data)
        assert item.id == "apple_001"
        assert item.name == "Organic Apples"
        assert item.description == "Fresh organic apples from local farm"
        assert item.price == 3.99
        assert isinstance(item.unit, XUnit)
        assert item.unit.symbol == "kg"
        assert item.group_id == "fruits"
        assert item.subgroup_id == "apples"
        assert item.is_available is True
        assert item.image_url == "https://example.com/apple.jpg"

    def test_item_model_minimal(self):
        """Test Item model with required fields only."""
        item_data = {"id": "item_123", "name": "Test Item"}
        item = Item(**item_data)
        assert item.id == "item_123"
        assert item.name == "Test Item"
        assert item.description is None
        assert item.price is None
        assert item.unit is None
        assert item.group_id is None
        assert item.subgroup_id is None
        assert item.is_available is True  # Default value
        assert item.image_url is None

    def test_article_model(self):
        """Test Article model creation."""
        article_data = {
            "id": "article_001",
            "name": "Apple Products",
            "description": "Collection of apple products",
            "items": [
                {"id": "apple_red", "name": "Red Apples"},
                {"id": "apple_green", "name": "Green Apples"},
            ],
        }
        article = Article(**article_data)
        assert article.id == "article_001"
        assert article.name == "Apple Products"
        assert article.description == "Collection of apple products"
        assert len(article.items) == 2
        assert isinstance(article.items[0], Item)
        assert article.items[0].name == "Red Apples"

    def test_cart_item_model(self):
        """Test CartItem model creation."""
        cart_item_data = {
            "item_id": "apple_001",
            "quantity": 2.5,
            "unit_price": 3.99,
            "total_price": 9.98,
            "item": {"id": "apple_001", "name": "Organic Apples"},
        }
        cart_item = CartItem(**cart_item_data)
        assert cart_item.item_id == "apple_001"
        assert cart_item.quantity == 2.5
        assert cart_item.unit_price == 3.99
        assert cart_item.total_price == 9.98
        assert isinstance(cart_item.item, Item)
        assert cart_item.item.name == "Organic Apples"

    def test_cart_item_model_minimal(self):
        """Test CartItem model with required fields only."""
        cart_item_data = {"item_id": "item_123", "quantity": 1.0}
        cart_item = CartItem(**cart_item_data)
        assert cart_item.item_id == "item_123"
        assert cart_item.quantity == 1.0
        assert cart_item.unit_price is None
        assert cart_item.total_price is None
        assert cart_item.item is None

    def test_position_model(self):
        """Test Position model creation."""
        position_data = {
            "id": "pos_001",
            "item_id": "apple_001",
            "quantity": 2.0,
            "unit_price": 3.99,
            "total_price": 7.98,
            "item": {"id": "apple_001", "name": "Organic Apples"},
        }
        position = Position(**position_data)
        assert position.id == "pos_001"
        assert position.item_id == "apple_001"
        assert position.quantity == 2.0
        assert position.unit_price == 3.99
        assert position.total_price == 7.98
        assert isinstance(position.item, Item)

    def test_discount_model(self):
        """Test Discount model creation."""
        discount_data = {
            "id": "discount_001",
            "name": "Early Bird Discount",
            "amount": 5.0,
            "percentage": 10.0,
            "code": "EARLY10",
        }
        discount = Discount(**discount_data)
        assert discount.id == "discount_001"
        assert discount.name == "Early Bird Discount"
        assert discount.amount == 5.0
        assert discount.percentage == 10.0
        assert discount.code == "EARLY10"

    def test_voucher_model(self):
        """Test Voucher model creation."""
        voucher_data = {
            "id": "voucher_001",
            "code": "SAVE20",
            "name": "20% Off Voucher",
            "discount_amount": 10.0,
            "discount_percentage": 20.0,
            "valid_from": "2023-01-01T00:00:00Z",
            "valid_until": "2023-12-31T23:59:59Z",
            "is_active": True,
        }
        voucher = Voucher(**voucher_data)
        assert voucher.id == "voucher_001"
        assert voucher.code == "SAVE20"
        assert voucher.name == "20% Off Voucher"
        assert voucher.discount_amount == 10.0
        assert voucher.discount_percentage == 20.0
        assert isinstance(voucher.valid_from, datetime)
        assert isinstance(voucher.valid_until, datetime)
        assert voucher.is_active is True

    def test_order_model(self):
        """Test Order model creation."""
        order_data = {
            "id": "order_001",
            "customer_id": "customer_123",
            "status": "confirmed",
            "order_date": "2023-10-15T10:00:00Z",
            "delivery_date": "2023-10-16T14:00:00Z",
            "positions": [
                {
                    "item_id": "apple_001",
                    "quantity": 2.0,
                    "unit_price": 3.99,
                    "total_price": 7.98,
                }
            ],
            "total_amount": 7.98,
            "discounts": [{"name": "First Order", "amount": 1.0}],
            "delivery_address": {"street": "123 Main St", "city": "Berlin"},
        }
        order = Order(**order_data)
        assert order.id == "order_001"
        assert order.customer_id == "customer_123"
        assert order.status == "confirmed"
        assert isinstance(order.order_date, datetime)
        assert isinstance(order.delivery_date, datetime)
        assert len(order.positions) == 1
        assert isinstance(order.positions[0], Position)
        assert order.total_amount == 7.98
        assert len(order.discounts) == 1
        assert isinstance(order.discounts[0], Discount)
        assert isinstance(order.delivery_address, Address)

    def test_delivery_state_enum(self):
        """Test DeliveryState enum values."""
        assert DeliveryState.PLANNED == "planned"
        assert DeliveryState.IN_PROGRESS == "in_progress"
        assert DeliveryState.DELIVERED == "delivered"
        assert DeliveryState.FAILED == "failed"

    def test_delivery_model(self):
        """Test Delivery model creation."""
        delivery_data = {
            "id": "delivery_001",
            "order_id": "order_001",
            "status": DeliveryState.PLANNED,
            "planned_date": "2023-10-16T14:00:00Z",
            "delivery_address": {"street": "123 Main St", "city": "Berlin"},
            "tracking_info": "TRACK123",
        }
        delivery = Delivery(**delivery_data)
        assert delivery.id == "delivery_001"
        assert delivery.order_id == "order_001"
        assert delivery.status == DeliveryState.PLANNED
        assert isinstance(delivery.planned_date, datetime)
        assert delivery.actual_date is None
        assert isinstance(delivery.delivery_address, Address)
        assert delivery.tracking_info == "TRACK123"

    def test_tour_model(self):
        """Test Tour model creation."""
        tour_data = {
            "id": "tour_001",
            "name": "Morning Route",
            "date": "2023-10-16T08:00:00Z",
            "deliveries": [
                {
                    "id": "delivery_001",
                    "order_id": "order_001",
                    "status": DeliveryState.PLANNED,
                }
            ],
        }
        tour = Tour(**tour_data)
        assert tour.id == "tour_001"
        assert tour.name == "Morning Route"
        assert isinstance(tour.date, datetime)
        assert len(tour.deliveries) == 1
        assert isinstance(tour.deliveries[0], Delivery)

    def test_subscription_model(self):
        """Test Subscription model creation."""
        subscription_data = {
            "id": "sub_001",
            "customer_id": "customer_123",
            "items": [{"item_id": "apple_001", "quantity": 2.0}],
            "frequency": "weekly",
            "next_delivery": "2023-10-16T14:00:00Z",
            "is_active": True,
            "is_paused": False,
        }
        subscription = Subscription(**subscription_data)
        assert subscription.id == "sub_001"
        assert subscription.customer_id == "customer_123"
        assert len(subscription.items) == 1
        assert isinstance(subscription.items[0], CartItem)
        assert subscription.frequency == "weekly"
        assert isinstance(subscription.next_delivery, datetime)
        assert subscription.is_active is True
        assert subscription.is_paused is False

    def test_favourite_model(self):
        """Test Favourite model creation."""
        favourite_data = {
            "customer_id": "customer_123",
            "item_id": "apple_001",
            "added_date": "2023-10-15T10:00:00Z",
        }
        favourite = Favourite(**favourite_data)
        assert favourite.customer_id == "customer_123"
        assert favourite.item_id == "apple_001"
        assert isinstance(favourite.added_date, datetime)

    def test_favourite_model_minimal(self):
        """Test Favourite model with required fields only."""
        favourite_data = {"customer_id": "customer_123", "item_id": "apple_001"}
        favourite = Favourite(**favourite_data)
        assert favourite.customer_id == "customer_123"
        assert favourite.item_id == "apple_001"
        assert favourite.added_date is None

    def test_box_model(self):
        """Test Box model creation."""
        box_data = {
            "id": "box_001",
            "name": "Large Box",
            "capacity": 15.0,
            "is_returnable": True,
        }
        box = Box(**box_data)
        assert box.id == "box_001"
        assert box.name == "Large Box"
        assert box.capacity == 15.0
        assert box.is_returnable is True

    def test_box_model_minimal(self):
        """Test Box model with required fields only."""
        box_data = {"id": "box_002", "name": "Small Box"}
        box = Box(**box_data)
        assert box.id == "box_002"
        assert box.name == "Small Box"
        assert box.capacity is None
        assert box.is_returnable is False  # Default value

    def test_ddate_model(self):
        """Test DDate model creation."""
        date_data = {
            "date": "2023-10-16T14:00:00Z",
            "is_available": True,
            "delivery_slots": ["morning", "afternoon", "evening"],
        }
        ddate = DDate(**date_data)
        assert isinstance(ddate.date, datetime)
        assert ddate.is_available is True
        assert len(ddate.delivery_slots) == 3
        assert "morning" in ddate.delivery_slots

    def test_ddate_model_minimal(self):
        """Test DDate model with required fields only."""
        date_data = {"date": "2023-10-16T14:00:00Z"}
        ddate = DDate(**date_data)
        assert isinstance(ddate.date, datetime)
        assert ddate.is_available is True  # Default value
        assert len(ddate.delivery_slots) == 0  # Default empty list

    def test_navigation_model(self):
        """Test Navigation model creation."""
        nav_data = {
            "id": "nav_001",
            "name": "Products",
            "url": "/products",
            "parent_id": "main_menu",
            "children": [
                {"id": "nav_002", "name": "Fruits", "url": "/products/fruits"}
            ],
        }
        nav = Navigation(**nav_data)
        assert nav.id == "nav_001"
        assert nav.name == "Products"
        assert nav.url == "/products"
        assert nav.parent_id == "main_menu"
        assert len(nav.children) == 1
        assert isinstance(nav.children[0], Navigation)
        assert nav.children[0].name == "Fruits"

    def test_api_response_model(self):
        """Test APIResponse model creation."""
        response_data = {
            "success": True,
            "data": {"items": [{"id": "item_1", "name": "Apple"}]},
            "message": "Success",
            "errors": [],
        }
        response = APIResponse(**response_data)
        assert response.success is True
        assert response.data == {"items": [{"id": "item_1", "name": "Apple"}]}
        assert response.message == "Success"
        assert len(response.errors) == 0

    def test_api_response_model_error(self):
        """Test APIResponse model with errors."""
        response_data = {
            "success": False,
            "message": "Validation failed",
            "errors": ["Invalid item ID", "Missing quantity"],
        }
        response = APIResponse(**response_data)
        assert response.success is False
        assert response.data is None
        assert response.message == "Validation failed"
        assert len(response.errors) == 2
        assert "Invalid item ID" in response.errors

    def test_api_response_model_minimal(self):
        """Test APIResponse model with defaults."""
        response = APIResponse()
        assert response.success is True  # Default value
        assert response.data is None
        assert response.message is None
        assert len(response.errors) == 0  # Default empty list
