"""Data models for the Ökobox Online API."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Shop(BaseModel):
    """Shop information from the shop list."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    latitude: float
    longitude: float
    delivery_lat: float | None = None
    delivery_lng: float | None = None


class Address(BaseModel):
    """Customer address information."""

    model_config = ConfigDict(from_attributes=True)

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class UserInfo(BaseModel):
    """User account information."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool = True
    pcgif_version: str | None = None
    shop_version: str | None = None


class CustomerInfo(BaseModel):
    """Customer profile information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_info: UserInfo
    address: Address | None = None


class Group(BaseModel):
    """Product group/category information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    info: str | None = None
    count: int = 0


class SubGroup(BaseModel):
    """Product subgroup information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    parent_id: str
    count: int = 0


class Item(BaseModel):
    """Product item information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: float | None = None
    description: str | None = None
    group_id: str | None = None
    subgroup_id: str | None = None
    unit: str | None = None
    is_available: bool = True
    image_url: str | None = None


class CartItem(BaseModel):
    """Shopping cart item."""

    model_config = ConfigDict(from_attributes=True)

    item_id: str
    quantity: float = 1.0
    unit: str | None = None
    price: float | None = None
    unit_price: float | None = None
    total_price: float | None = None
    note: str | None = None


class DDate(BaseModel):
    """Delivery date information."""

    model_config = ConfigDict(from_attributes=True)

    date: datetime
    is_available: bool = True
    delivery_slots: list[str] = Field(default_factory=list)


class Subscription(BaseModel):
    """Customer subscription information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    frequency: str | None = None
    is_active: bool = True
    next_delivery: date | None = None


class Favourite(BaseModel):
    """Customer favourite item."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    item_id: str


class Order(BaseModel):
    """Customer order information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    delivery_date: date | None = None
    status: str | None = None
    total: float | None = None
    items: list[CartItem] = Field(default_factory=list)


# Additional models that might be used by the API
class APIResponse(BaseModel):
    """Generic API response."""

    model_config = ConfigDict(from_attributes=True)

    action: str | None = None
    result: str | None = None
    data: Any = None


class Navigation(BaseModel):
    """Navigation menu item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: str | None = None


class DeliveryState(str, Enum):
    """Delivery state enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Delivery(BaseModel):
    """Delivery information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    delivery_date: date
    state: DeliveryState
    address: Address | None = None


class Position(BaseModel):
    """Order position/line item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    quantity: float
    unit_price: float
    total_price: float


class Article(BaseModel):
    """Article/product detailed information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    price: float
    unit: str | None = None
    category: str | None = None


class Box(BaseModel):
    """Subscription box information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    price: float
    items: list[Item] = Field(default_factory=list)


class Tour(BaseModel):
    """Delivery tour information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    delivery_date: date
    addresses: list[Address] = Field(default_factory=list)


class Discount(BaseModel):
    """Discount information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    amount: float
    percentage: float | None = None


class Voucher(BaseModel):
    """Voucher information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    value: float
    is_valid: bool = True


class XUnit(BaseModel):
    """Extended unit information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    abbreviation: str
    factor: float = 1.0
