"""Data models for the Ökobox Online API."""

from datetime import datetime
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
    # Secondary coordinates (possibly delivery area center)
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


class CustomerInfo(BaseModel):
    """Customer information."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    user_info: UserInfo | None = None
    delivery_address: Address | None = None
    billing_address: Address | None = None


class XUnit(BaseModel):
    """Pricing unit information."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    name: str | None = None
    symbol: str | None = None


class Group(BaseModel):
    """Product group/category."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    parent_id: str | None = None


class SubGroup(BaseModel):
    """Product subcategory."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    group_id: str | None = None


class Item(BaseModel):
    """Individual product item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    price: float | None = None
    unit: XUnit | None = None
    group_id: str | None = None
    subgroup_id: str | None = None
    is_available: bool = True
    image_url: str | None = None


class Article(BaseModel):
    """Product article information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    items: list[Item] = Field(default_factory=list)


class CartItem(BaseModel):
    """Item in shopping cart."""

    model_config = ConfigDict(from_attributes=True)

    item_id: str
    quantity: float
    unit_price: float | None = None
    total_price: float | None = None
    item: Item | None = None


class Position(BaseModel):
    """Order line item position."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    item_id: str
    quantity: float
    unit_price: float
    total_price: float
    item: Item | None = None


class Discount(BaseModel):
    """Price discount information."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    name: str | None = None
    amount: float | None = None
    percentage: float | None = None
    code: str | None = None


class Voucher(BaseModel):
    """Discount voucher/coupon."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str | None = None
    discount_amount: float | None = None
    discount_percentage: float | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True


class Order(BaseModel):
    """Customer order."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    status: str | None = None
    order_date: datetime | None = None
    delivery_date: datetime | None = None
    positions: list[Position] = Field(default_factory=list)
    total_amount: float | None = None
    discounts: list[Discount] = Field(default_factory=list)
    delivery_address: Address | None = None


class DeliveryState(str, Enum):
    """Delivery status options."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    FAILED = "failed"


class Delivery(BaseModel):
    """Delivery information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    status: DeliveryState
    planned_date: datetime | None = None
    actual_date: datetime | None = None
    delivery_address: Address | None = None
    tracking_info: str | None = None


class Tour(BaseModel):
    """Delivery tour/route."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None = None
    date: datetime | None = None
    deliveries: list[Delivery] = Field(default_factory=list)


class Subscription(BaseModel):
    """Recurring delivery subscription."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    items: list[CartItem] = Field(default_factory=list)
    frequency: str | None = None  # weekly, monthly, etc.
    next_delivery: datetime | None = None
    is_active: bool = True
    is_paused: bool = False


class Favourite(BaseModel):
    """Customer favorite item."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    item_id: str
    added_date: datetime | None = None


class Box(BaseModel):
    """Delivery packaging box."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    capacity: float | None = None
    is_returnable: bool = False


class DDate(BaseModel):
    """Delivery date information."""

    model_config = ConfigDict(from_attributes=True)

    date: datetime
    is_available: bool = True
    delivery_slots: list[str] = Field(default_factory=list)


class Navigation(BaseModel):
    """Site navigation structure."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: str | None = None
    parent_id: str | None = None
    children: list["Navigation"] = Field(default_factory=list)


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    data: Any | None = None
    message: str | None = None
    errors: list[str] = Field(default_factory=list)
