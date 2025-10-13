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

    # Core user identification
    authentication_state: str | None = (
        None  # Position 1: NONE, INVALID, VALID, AUTH, SUPER, ADMIN
    )
    id: str | None = None  # Position 2: userid
    opener: str | None = None  # Position 3: title/addressing opener
    first_name: str | None = None  # Position 4: firstname
    last_name: str | None = None  # Position 5: lastname

    # User role and permissions
    role: int | None = None  # Position 6: 0=customer, 1=Web-Admin, 2=Driver, etc.
    debug_level: int | None = None  # Position 7: debug level for client app

    # Driver-specific settings (positions 8-12)
    driver_load: int | None = None  # Position 8
    driver_serve: int | None = None  # Position 9
    driver_next: int | None = None  # Position 10
    driver_next_load: int | None = None  # Position 11
    driver_tracking: int | None = None  # Position 12

    # User preferences
    pref_asdc: int | None = None  # Position 13: auto-submit changed orders

    # Contact information
    email: str | None = None  # Position 14: primary email
    email1: str | None = None  # Position 15: secondary email
    phone: str | None = None  # Position 16: primary phone
    phone1: str | None = None  # Position 17: secondary phone/mobile

    # Address information
    country: str | None = None  # Position 18: ISO country code
    zip: str | None = None  # Position 19: ZIP code
    city: str | None = None  # Position 20: city
    street: str | None = None  # Position 21: street address

    # Payment information
    account_no: str | None = None  # Position 22: account number
    paycode: int | None = None  # Position 23: payment option

    # Customer notes and preferences
    note: str | None = None  # Position 24: customer note
    placecode: int | None = None  # Position 25: storage codes
    sepa_info: str | None = None  # Position 26: SEPA mandate info

    # Delivery address (positions 27-30)
    delivery_name: str | None = None  # Position 27
    delivery_zip: str | None = None  # Position 28
    delivery_city: str | None = None  # Position 29
    delivery_street: str | None = None  # Position 30

    # Company information
    company: str | None = None  # Position 31: company name
    no_ad: int | None = None  # Position 32: no advertisements flag
    place_note: str | None = None  # Position 33: delivery placement note

    # Additional preferences and settings
    pref_abocart: int | None = None  # Position 34: show inactive subscription positions
    pref_partial: int | None = None  # Position 35: show partial delivery pauses
    department: str | None = None  # Position 36: customer department
    vat_id: str | None = None  # Position 37: VAT ID
    delivery_company: str | None = None  # Position 38: delivery company
    delivery_department: str | None = None  # Position 39: delivery department
    driver_note: str | None = None  # Position 40: driver notes
    balance: float | None = None  # Position 41: account balance
    trace_me: int | None = None  # Position 42: analytics tracking denied
    trivial_warning: int | None = None  # Position 43: simple password warning
    order_limit: float | None = None  # Position 44: order limit
    needs_tc: int | None = None  # Position 45: needs T&C reconfirmation
    bic: str | None = None  # Position 46: BIC banking code
    is_active: bool = True  # Position 47: customer active status
    box_cnt: int | None = None  # Position 48: refund boxes count
    rgroup_until: str | None = None  # Position 49: discount group membership

    # Notification settings (positions 50-57)
    notification_order: str | None = None  # Position 50: order confirmation
    notification_cart: str | None = None  # Position 51: cart forgotten reminder
    notification_delivery: str | None = None  # Position 52: delivery notice
    notification_ochange: str | None = None  # Position 53: order changed
    notification_reminder: str | None = None  # Position 54: deadline reminder
    notification_profile: str | None = None  # Position 55: profile changed
    notification_newsletter: str | None = None  # Position 56: newsletter
    notification_refund: str | None = None  # Position 57: refund processed

    # Additional fields
    no_refund: int | None = None  # Position 58: no refund invoicing
    has_orders: int | None = None  # Position 59: has orders in system
    special_items: list[str] | None = None  # Position 60: special price items array

    # Legacy fields for backward compatibility
    username: str | None = None  # Derived from opener or email
    pcgif_version: str | None = None  # Legacy field
    shop_version: str | None = None  # Legacy field

    @classmethod
    def from_api_array(cls, data: list[Any]) -> "UserInfo":
        """Create UserInfo from API positional array format.

        Based on the official API documentation at:
        https://oekobox-online.de/shopdocu/wiki/API.objects.UserInfo

        Args:
            data: Positional array from API response

        Returns:
            UserInfo instance with mapped fields
        """
        if not data or len(data) == 0:
            return cls()

        user_info = cls()

        try:
            # Map each position according to the official documentation
            if len(data) > 0 and data[0] is not None:
                user_info.authentication_state = str(data[0])

            if len(data) > 1 and data[1] is not None:
                user_info.id = str(data[1])

            if len(data) > 2 and data[2] is not None:
                user_info.opener = str(data[2])

            if len(data) > 3 and data[3] is not None:
                user_info.first_name = str(data[3])

            if len(data) > 4 and data[4] is not None:
                user_info.last_name = str(data[4])

            if len(data) > 5 and data[5] is not None:
                user_info.role = int(data[5]) if str(data[5]).isdigit() else None

            if len(data) > 6 and data[6] is not None:
                user_info.debug_level = int(data[6]) if str(data[6]).isdigit() else None

            if len(data) > 7 and data[7] is not None:
                user_info.driver_load = int(data[7]) if str(data[7]).isdigit() else None

            if len(data) > 8 and data[8] is not None:
                user_info.driver_serve = (
                    int(data[8]) if str(data[8]).isdigit() else None
                )

            if len(data) > 9 and data[9] is not None:
                user_info.driver_next = int(data[9]) if str(data[9]).isdigit() else None

            # Continue mapping more positions as needed based on actual response length
            if len(data) > 13 and data[13] is not None:
                user_info.email = str(data[13])

            if len(data) > 14 and data[14] is not None:
                user_info.email1 = str(data[14])

            if len(data) > 15 and data[15] is not None:
                user_info.phone = str(data[15])

            if len(data) > 16 and data[16] is not None:
                user_info.phone1 = str(data[16])

            if len(data) > 17 and data[17] is not None:
                user_info.country = str(data[17])

            if len(data) > 18 and data[18] is not None:
                user_info.zip = str(data[18])

            if len(data) > 19 and data[19] is not None:
                user_info.city = str(data[19])

            if len(data) > 20 and data[20] is not None:
                user_info.street = str(data[20])

            # Set derived fields for compatibility
            user_info.username = user_info.email or user_info.opener or user_info.id

            # Set active status - user is active if they have an authentication state
            user_info.is_active = user_info.authentication_state not in [
                None,
                "NONE",
                "INVALID",
            ]

        except (IndexError, ValueError, TypeError):
            # If parsing fails, return basic UserInfo with available data
            pass

        return user_info


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
