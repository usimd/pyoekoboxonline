"""Python client for the Ökobox Online REST API."""

from .client import OekoboxClient
from .exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxError,
    OekoboxValidationError,
)
from .models import (
    Address,
    CartItem,
    CustomerInfo,
    DataListModel,
    DataListResponse,
    DDate,
    Favourite,
    Group,
    Item,
    Order,
    Shop,
    SubGroup,
    Subscription,
    UserInfo,
    parse_data_list_response,
)

__version__ = "0.1.0b4"

__all__ = [
    "Address",
    "CartItem",
    "CustomerInfo",
    "DDate",
    "DataListModel",
    "DataListResponse",
    "Favourite",
    "Group",
    "Item",
    "OekoboxAPIError",
    "OekoboxAuthenticationError",
    "OekoboxClient",
    "OekoboxConnectionError",
    "OekoboxError",
    "OekoboxValidationError",
    "Order",
    "Shop",
    "SubGroup",
    "Subscription",
    "UserInfo",
    "parse_data_list_response",
]
