"""
Unit tests for the pyoekoboxonline models.

Tests the DataListModel base class functionality and specific model implementations.
"""

from dataclasses import dataclass, field

import pytest

from pyoekoboxonline.models import (
    MODEL_REGISTRY,
    Address,
    DataListModel,
    DataListResponse,
    Group,
    Item,
    Order,
    UserInfo,
    XUnit,
    parse_data_list_response,
)


class TestDataListModel:
    """Test the DataListModel base class functionality."""

    def test_from_data_list_entry_requires_dataclass(self):
        """Test that from_data_list_entry requires a dataclass."""

        class NotADataclass(DataListModel):
            pass

        with pytest.raises(ValueError, match="must be a dataclass"):
            NotADataclass.from_data_list_entry([])

    def test_from_data_list_entry_basic_functionality(self):
        """Test basic functionality of from_data_list_entry."""

        @dataclass
        class TestModel(DataListModel):
            id: int | None = field(default=None)
            name: str | None = field(default=None)
            price: float | None = field(default=None)

        data = [123, "Test Item", 45.99]
        instance = TestModel.from_data_list_entry(data)

        assert instance.id == 123
        assert instance.name == "Test Item"
        assert instance.price == 45.99

    def test_from_data_list_entry_with_missing_data(self):
        """Test handling of missing data in array."""

        @dataclass
        class TestModel(DataListModel):
            id: int | None = field(default=None)
            name: str | None = field(default=None)
            price: float | None = field(default=None)
            description: str | None = field(default=None)

        # Data array shorter than expected fields
        data = [123, "Test Item"]
        instance = TestModel.from_data_list_entry(data)

        assert instance.id == 123
        assert instance.name == "Test Item"
        assert instance.price is None
        assert instance.description is None

    def test_from_data_list_entry_with_empty_values(self):
        """Test handling of empty/null values."""

        @dataclass
        class TestModel(DataListModel):
            id: int | None = field(default=None)
            name: str | None = field(default=None)
            price: float | None = field(default=None)

        data = [123, "", None]
        instance = TestModel.from_data_list_entry(data)

        assert instance.id == 123
        assert instance.name is None
        assert instance.price is None

    def test_from_data_list_entry_type_conversions(self):
        """Test automatic type conversions."""

        @dataclass
        class TestModel(DataListModel):
            id: int | None = field(default=None)
            active: bool | None = field(default=None)
            price: float | None = field(default=None)
            name: str | None = field(default=None)

        data = ["123", "1", "45.99", 456]  # String inputs that need conversion
        instance = TestModel.from_data_list_entry(data)

        assert instance.id == 123
        assert instance.active is True
        assert instance.price == 45.99
        assert instance.name == "456"

    def test_from_data_list_entry_conversion_failures(self):
        """Test handling of type conversion failures."""

        @dataclass
        class TestModel(DataListModel):
            id: int | None = field(default=None)
            price: float | None = field(default=None)

        data = ["not_a_number", "also_not_a_number"]
        instance = TestModel.from_data_list_entry(data)

        # Failed conversions should result in None
        assert instance.id is None
        assert instance.price is None


class TestSpecificModels:
    """Test specific model implementations."""

    def test_item_model_creation(self):
        """Test Item model creation from data list entry."""
        data = [
            1,
            "Apple",
            2.50,
            "kg",
            "Fresh red apples",
            1,
            7.0,
            0,
            0.25,
            "S",
            "0",
            "2.30",
            "hash123",
            "1",
            1,
            1,
            "2024-01-01",
            "2024-01-31",
            "2024-01-01",
            "2024-01-31",
            "0",
            1,
            0,
            1,
            "apple fruit",
            "kg",
            "hash456",
            "Test Pack",
            "Organic",
            "Local Farm",
            1,
            1.0,
            5.0,
            1.0,
            0.5,
            3,
            2.0,
            "bio,organic",
            1,
            1,
            1,
            0,
            "Delicious",
            1,
            "piece",
            0,
            "EU:Organic",
            0,
            "Class I",
            1,
            1,
            2.5,
            1.2,
            90,
            "500g pack",
            2.0,
            2.0,
            "2.00",
            0,
            "2024-12-31",
            "Apple Brand",
            "EAN123456",
            "Producer Name",
            0,
            "Brand Name",
        ]

        item = Item.from_data_list_entry(data)

        assert item.id == 1
        assert item.name == "Apple"
        assert item.price == 2.50
        assert item.unit == "kg"
        assert item.description == "Fresh red apples"

    def test_group_model_creation(self):
        """Test Group model creation from data list entry."""
        data = [1, "Fruits", "Fresh fruits category", 25, 5, "bio,organic", 1, 1]

        group = Group.from_data_list_entry(data)

        assert group.id == 1
        assert group.name == "Fruits"
        assert group.infotext == "Fresh fruits category"
        assert group.count == 25
        assert group.subgroup_count == 5

    def test_order_model_creation(self):
        """Test Order model creation from data list entry."""
        data = [
            123,
            "2024-01-15",
            "0",
            1,
            "Customer note",
            "Delivery note",
            "14:00",
            "2024-01-14T10:00:00",
            1,
            5.0,
            0,
            1,
            100,
            "CODE123",
            1,
            456,
            125.50,
        ]

        order = Order.from_data_list_entry(data)

        assert order.id == 123
        assert order.ddate == "2024-01-15"
        assert order.state == "0"
        assert order.tour_id == 1
        assert order.cnote == "Customer note"
        assert order.rnote == "Delivery note"

    def test_address_model_creation(self):
        """Test Address model creation from data list entry."""
        data = [
            100,
            "home",
            "Smith",
            "John",
            "123 Main St",
            "Berlin",
            "12345",
            "12345",
            52.5200,
            13.4050,
            95,
            "+49301234567",
            "+49151234567",
            "Ring doorbell",
            "Use main entrance",
            "Handle with care",
        ]

        address = Address.from_data_list_entry(data)

        assert address.customer_id == 100
        assert address.address_name == "home"
        assert address.name == "Smith"
        assert address.firstname == "John"
        assert address.street == "123 Main St"
        assert address.city == "Berlin"
        assert address.zip == "12345"

    def test_userinfo_model_creation(self):
        """Test UserInfo model creation from data list entry."""
        data = [
            "AUTH",
            123,
            "Dear",
            "John",
            "Smith",
            "0",
            "0",
            "0",
            "0",
            0,
            "0",
            "1",
            "1",
            "john@example.com",
            0,
            "+49301234567",
            "+49151234567",
            "DE",
            "12345",
            "Berlin",
            "Main St 123",
            1234567890,
            1,
            "Customer note",
            "123",
            "SEPA123",
            "Jane Smith",
            "54321",
            "Munich",
            "Other St 456",
            "ACME Corp",
            0,
            "Garage",
            0,
            0,
            "IT",
            "DE123456789",
            "ACME Delivery",
            "Shipping",
            "Handle with care",
            150.0,
            0,
            0,
            1000.0,
            0,
            "DEUTDEFF",
            1,
            2,
            "2024-12-31",
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            0,
            1,
        ]

        user_info = UserInfo.from_data_list_entry(data)

        assert user_info.authentication_state == "AUTH"
        assert user_info.user_id == 123
        assert user_info.opener == "Dear"
        assert user_info.firstname == "John"
        assert user_info.lastname == "Smith"

    def test_xunit_model_creation(self):
        """Test XUnit model creation from data list entry."""
        data = [1, "piece", "1", "S", 1, "1"]

        xunit = XUnit.from_data_list_entry(data)

        assert xunit.item_id == 1
        assert xunit.name == "piece"
        assert xunit.parts == "1"
        assert xunit.type == "S"
        assert xunit.unit_id == 1
        assert xunit.preferred == "1"


class TestParseDataListResponse:
    """Test the parse_data_list_response function."""

    def test_parse_simple_response(self):
        """Test parsing a simple DataList response."""
        response_data = [
            {
                "type": "Group",
                "data": [
                    [1, "Fruits", "Fresh fruits", 25, 5, "bio", 1, 1],
                    [2, "Vegetables", "Fresh vegetables", 30, 8, "organic", 0, 1],
                    [0],  # Terminating entry
                ],
            }
        ]

        result = parse_data_list_response(response_data)

        assert len(result) == 2
        assert all(isinstance(item, Group) for item in result)
        assert result[0].id == 1
        assert result[0].name == "Fruits"
        assert result[1].id == 2
        assert result[1].name == "Vegetables"

    def test_parse_mixed_types_response(self):
        """Test parsing response with multiple object types."""
        response_data = [
            {
                "type": "Group",
                "data": [
                    [1, "Fruits", "Fresh fruits", 25, 5, "bio", 1, 1],
                    [0],
                ],
            },
            {
                "type": "Item",
                "data": [
                    [1, "Apple", 2.50, "kg", "Fresh red apples", 1, 7.0],
                    [0],
                ],
            },
        ]

        result = parse_data_list_response(response_data)

        assert len(result) == 2
        groups = [r for r in result if isinstance(r, Group)]
        items = [r for r in result if isinstance(r, Item)]
        assert len(groups) == 1
        assert len(items) == 1

    def test_parse_empty_response(self):
        """Test parsing empty response."""
        response_data = []
        result = parse_data_list_response(response_data)
        assert result == []

    def test_parse_unknown_type(self):
        """Test parsing response with unknown object type."""
        response_data = [
            {
                "type": "UnknownType",
                "data": [
                    [1, "Some data"],
                    [0],
                ],
            }
        ]

        result = parse_data_list_response(response_data)
        # Unknown types should be skipped
        assert result == []

    def test_parse_malformed_response(self):
        """Test parsing malformed response data."""
        response_data = [
            "not_a_dict",
            {"no_type_field": True},
            {
                "type": "Foo",
                "data": [
                    "malformed_data_entry",
                    [0],
                ],
            },
        ]

        result = parse_data_list_response(response_data)
        # Malformed entries should be skipped gracefully
        assert result == []

    def test_model_registry_completeness(self):
        """Test that MODEL_REGISTRY contains expected models."""
        expected_models = [
            "Address",
            "Item",
            "Group",
            "Order",
            "UserInfo",
            "XUnit",
            "Tour",
            "DDate",
            "Delivery",
            "Subscription",
            "CartItem",
        ]

        for model_name in expected_models:
            assert model_name in MODEL_REGISTRY, (
                f"Missing {model_name} in MODEL_REGISTRY"
            )

    def test_datalist_response_structure(self):
        """Test DataListResponse structure."""
        response = DataListResponse(
            type="Group", version=1, cnt=2, data=[[1, "Test"], [2, "Another"]]
        )

        assert response.type == "Group"
        assert response.version == 1
        assert response.cnt == 2
        assert len(response.data) == 2
