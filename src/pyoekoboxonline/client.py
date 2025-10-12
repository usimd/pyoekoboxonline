"""Main client for the Ökobox Online API."""

import logging
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .exceptions import (
    OekoboxAPIError,
    OekoboxAuthenticationError,
    OekoboxConnectionError,
    OekoboxValidationError,
)
from .models import (
    CartItem,
    CustomerInfo,
    DDate,
    Favourite,
    Group,
    Item,
    Order,
    Shop,
    SubGroup,
    Subscription,
    UserInfo,
)

logger = logging.getLogger(__name__)


class OekoboxClient:
    """Async client for the Ökobox Online REST API.

    This client provides methods to interact with the Ökobox Online e-commerce
    platform API for food delivery and subscription services.

    Args:
        shop_id: Shop identifier from the shop list
        username: Username for authentication
        password: Password for authentication
        base_url: Base URL of the shop (default: auto-detected from shop_id)
        timeout: Request timeout in seconds (default: 30)

    Example:
        ```python
        import asyncio
        from pyoekoboxonline import OekoboxClient

        async def main():
            # First, discover available shops
            shops = await OekoboxClient.get_available_shops()
            print(f"Found {len(shops)} shops")

            # Connect to a specific shop
            client = OekoboxClient(
                shop_id="lammertzhof",  # Example shop ID
                username="your-username",
                password="your-password"
            )

            async with client:
                # Login
                await client.login()

                # Browse products
                items = await client.get_items()
                for item in items:
                    print(f"{item.name}: {item.price}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        shop_id: str,
        username: str,
        password: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.shop_id = shop_id
        self.username = username
        self.password = password
        self.timeout = timeout

        # Auto-detect base URL if not provided
        if base_url is None:
            self.base_url = f"https://oekobox-online.de/v3/shop/{shop_id}"
        else:
            self.base_url = base_url.rstrip("/")

        self.session_id: str | None = None
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "pyoekoboxonline/0.1.0",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> "OekoboxClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.logout()
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        require_auth: bool = False,
    ) -> Any:
        """Make an HTTP request to the API."""
        url = self._build_url(endpoint)

        # Add session ID if available
        if params is None:
            params = {}
        if self.session_id:
            params["x-oekobox-sid"] = self.session_id

        # Add authentication check header if required
        headers = {"x-oo-auth": "1"} if require_auth else {}

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise OekoboxAuthenticationError(
                    "Authentication failed. Please check your credentials.",
                    status_code=response.status_code,
                )
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("message", f"HTTP {response.status_code}")
                except Exception:
                    message = f"HTTP {response.status_code}: {response.text}"

                raise OekoboxAPIError(
                    message=message,
                    status_code=response.status_code,
                    response_data=error_data if "error_data" in locals() else None,
                )

            # Parse JSON response
            try:
                return response.json()
            except Exception:
                # Some endpoints might return plain text
                return {"data": response.text}

        except httpx.RequestError as exc:
            raise OekoboxConnectionError(
                f"Connection error: {exc}",
                original_error=exc,
            ) from exc

    @staticmethod
    async def get_available_shops() -> list[Shop]:
        """Get list of available shops with geographical information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://oekobox-online.eu/v3/shoplist.js.jsp"
                )
                content = response.text

                shops = []
                # Parse the JavaScript array format
                for line in content.strip().split("\n"):
                    line = line.strip().rstrip(",")
                    if line.startswith("[") and line.endswith("]"):
                        try:
                            # Parse the array: [lat, lng, "name", lat2, lng2, "shop_id"]
                            match = re.match(
                                r'\[([-\d.]+),([-\d.]+),"([^"]+)",([-\d.]+),([-\d.]+),"([^"]+)"\]',
                                line,
                            )
                            if match:
                                lat, lng, name, lat2, lng2, shop_id = match.groups()

                                # Skip entries with invalid coordinates
                                if lat == "-1" or lng == "-1":
                                    lat, lng = lat2, lng2

                                shop = Shop(
                                    id=shop_id,
                                    name=name,
                                    latitude=float(lat),
                                    longitude=float(lng),
                                    delivery_lat=float(lat2) if lat2 != "-1" else None,
                                    delivery_lng=float(lng2) if lng2 != "-1" else None,
                                )
                                shops.append(shop)
                        except (ValueError, AttributeError):
                            continue

                return shops

            except Exception as e:
                raise OekoboxConnectionError(f"Failed to fetch shop list: {e}") from e

    # Authentication methods
    async def login(self) -> UserInfo:
        """Login with username and password."""
        try:
            response = await self._client.get(
                self._build_url("/logon"),
                params={
                    "cid": self.username,
                    "pass": self.password,
                },
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            raise OekoboxConnectionError(f"Failed to connect to API: {e}") from e

        # Handle HTTP errors
        if response.status_code == 401:
            raise OekoboxAuthenticationError(
                "Authentication failed. Please check your credentials.",
                status_code=response.status_code,
            )
        elif response.status_code >= 400:
            raise OekoboxAPIError(
                f"Login failed with status {response.status_code}",
                status_code=response.status_code,
            )

        # Extract session ID from cookies
        session_cookie = response.cookies.get("OOSESSION")
        if session_cookie:
            self.session_id = session_cookie
        else:
            raise OekoboxAuthenticationError(
                "Login successful but no session ID received",
                status_code=response.status_code,
            )

        # Parse response data
        try:
            data = response.json()
        except Exception:
            # If no JSON response, create minimal user info
            data = {
                "id": None,
                "username": self.username,
                "email": None,
                "is_active": True,
            }

        try:
            return UserInfo(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid user data: {exc}") from exc

    async def logout(self) -> None:
        """Logout and clear session."""
        if self.session_id:
            await self._request("GET", "/logout")
            self.session_id = None

    # User and customer methods
    async def get_user_info(self) -> UserInfo:
        """Get current user information."""
        data = await self._request("GET", "/api/user", require_auth=True)
        try:
            return UserInfo(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid user data: {exc}") from exc

    async def get_customer_info(self) -> CustomerInfo:
        """Get customer profile information."""
        data = await self._request("GET", "/api/client/state", require_auth=True)
        try:
            return CustomerInfo(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid customer data: {exc}") from exc

    # Product catalog methods
    async def get_groups(self) -> list[Group]:
        """Get product groups/categories."""
        data = await self._request("GET", "/api/groups")
        try:
            if isinstance(data, list):
                return [Group(**item) for item in data]
            else:
                return [Group(**item) for item in data.get("groups", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid group data: {exc}") from exc

    async def get_subgroups(self, group_id: str | None = None) -> list[SubGroup]:
        """Get product subgroups."""
        params = {"group_id": group_id} if group_id else {}
        data = await self._request("GET", "/api/subgroup", params=params)
        try:
            if isinstance(data, list):
                return [SubGroup(**item) for item in data]
            else:
                return [SubGroup(**item) for item in data.get("subgroups", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid subgroup data: {exc}") from exc

    async def get_items(
        self,
        group_id: str | None = None,
        subgroup_id: str | None = None,
    ) -> list[Item]:
        """Get available items/products."""
        params = {}
        if group_id:
            params["group_id"] = group_id
        if subgroup_id:
            params["subgroup_id"] = subgroup_id

        data = await self._request("GET", "/api/items", params=params)
        try:
            if isinstance(data, list):
                return [Item(**item) for item in data]
            else:
                return [Item(**item) for item in data.get("items", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid item data: {exc}") from exc

    async def get_item(self, item_id: str) -> Item:
        """Get details for a specific item."""
        data = await self._request("GET", "/api/item", params={"item_id": item_id})
        try:
            return Item(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid item data: {exc}") from exc

    async def search_items(self, query: str) -> list[Item]:
        """Search for items by name or description."""
        data = await self._request("GET", "/api/search", params={"q": query})
        try:
            if isinstance(data, list):
                return [Item(**item) for item in data]
            else:
                return [Item(**item) for item in data.get("items", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid search results: {exc}") from exc

    # Shopping cart methods
    async def get_cart(self) -> list[CartItem]:
        """Get current shopping cart contents."""
        data = await self._request("GET", "/api/cart/show", require_auth=True)
        try:
            if isinstance(data, list):
                return [CartItem(**item) for item in data]
            else:
                return [CartItem(**item) for item in data.get("cart_items", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid cart data: {exc}") from exc

    async def add_to_cart(self, item_id: str, quantity: float) -> None:
        """Add item to shopping cart."""
        await self._request(
            "POST",
            "/api/cart/add",
            json_data={"item_id": item_id, "quantity": quantity},
            require_auth=True,
        )

    async def remove_from_cart(self, item_id: str) -> None:
        """Remove item from shopping cart."""
        await self._request(
            "POST",
            "/api/cart/remove",
            json_data={"item_id": item_id},
            require_auth=True,
        )

    async def clear_cart(self) -> None:
        """Clear all items from shopping cart."""
        await self._request("POST", "/api/client/resetcart", require_auth=True)

    # Order methods
    async def create_order(self) -> Order:
        """Create order from current cart."""
        data = await self._request("POST", "/api/client/neworder", require_auth=True)
        try:
            return Order(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid order data: {exc}") from exc

    async def get_orders(self) -> list[Order]:
        """Get customer's orders."""
        data = await self._request("GET", "/api/orders", require_auth=True)
        try:
            if isinstance(data, list):
                return [Order(**item) for item in data]
            else:
                return [Order(**item) for item in data.get("orders", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid orders data: {exc}") from exc

    async def get_order(self, order_id: str) -> Order:
        """Get specific order details."""
        data = await self._request(
            "GET", "/api/order", params={"order_id": order_id}, require_auth=True
        )
        try:
            return Order(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid order data: {exc}") from exc

    # Delivery methods
    async def get_delivery_dates(self) -> list[DDate]:
        """Get available delivery dates."""
        data = await self._request("GET", "/api/dates")
        try:
            if isinstance(data, list):
                return [DDate(**item) for item in data]
            else:
                return [DDate(**item) for item in data.get("dates", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid delivery date data: {exc}") from exc

    # Subscription methods
    async def get_subscriptions(self) -> list[Subscription]:
        """Get customer's active subscriptions."""
        data = await self._request(
            "GET", "/api/client/subscriptions", require_auth=True
        )
        try:
            if isinstance(data, list):
                return [Subscription(**item) for item in data]
            else:
                return [Subscription(**item) for item in data.get("subscriptions", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid subscription data: {exc}") from exc

    async def add_subscription(
        self, items: list[CartItem], frequency: str
    ) -> Subscription:
        """Add new subscription."""
        data = await self._request(
            "POST",
            "/api/client/addsubscription",
            json_data={
                "items": [item.dict() for item in items],
                "frequency": frequency,
            },
            require_auth=True,
        )
        try:
            return Subscription(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid subscription data: {exc}") from exc

    # Favorites methods
    async def get_favourites(self) -> list[Favourite]:
        """Get customer's favorite items."""
        data = await self._request("GET", "/api/client/favourites", require_auth=True)
        try:
            if isinstance(data, list):
                return [Favourite(**item) for item in data]
            else:
                return [Favourite(**item) for item in data.get("favourites", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid favourites data: {exc}") from exc

    async def add_favourite(self, item_id: str) -> None:
        """Add item to favorites."""
        await self._request(
            "POST",
            "/api/client/addfavourites",
            json_data={"item_id": item_id},
            require_auth=True,
        )

    async def remove_favourite(self, item_id: str) -> None:
        """Remove item from favorites."""
        await self._request(
            "POST",
            "/api/client/dropfavourites",
            json_data={"item_id": item_id},
            require_auth=True,
        )
