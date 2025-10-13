"""Main client for the Ökobox Online API."""

import logging
import re
from contextlib import suppress
from datetime import datetime
from typing import Any

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

    Based on official API documentation from: https://oekobox-online.de/shopdocu/wiki/API

    Args:
        shop_id: Shop identifier from the shop list
        username: Username/Customer ID for authentication (can be email or customer ID)
        password: Password for authentication
        base_url: Base URL of the shop (default: auto-detected from shop_id)
        timeout: Request timeout in seconds (default: 30)

    Example:
        ```python
        import asyncio
        from pyoekoboxonline import OekoboxClient

        async def main():
            async with OekoboxClient("amperhof", "user@example.com", "password") as client:
                # Login using official 'logon' method
                user_info = await client.logon()

                # Get product groups
                groups = await client.get_groups()

                # Logout using official 'logout' method
                await client.logout()

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
        """Initialize the Ökobox Online client."""
        self.shop_id = shop_id
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session_id: str | None = None

        # Official API URL structure: https://oekobox-online.de/v3/shop/<shopid>/
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = f"https://oekobox-online.de/v3/shop/{shop_id}"

        # Initialize HTTP client
        self._client: httpx.AsyncClient | None = None

    @property
    def api_base_url(self) -> str:
        """Get the API base URL according to official specification."""
        return f"{self.base_url}/api"

    async def __aenter__(self) -> "OekoboxClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an HTTP request with proper session management.

        According to official API docs, sessions can be maintained via:
        1. Standard cookies (preferred)
        2. x-oekobox-sid parameter
        """
        if not self._client:
            raise OekoboxConnectionError(
                "Client not initialized. Use async context manager."
            )

        # Prepare headers
        headers = kwargs.get("headers", {})

        # Add session ID parameter if available (official API specification)
        if self.session_id:
            if params is None:
                params = {}
            params["x-oekobox-sid"] = self.session_id

        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                **kwargs,
            )

            # Extract session ID from various cookie formats
            if "Set-Cookie" in response.headers or response.cookies:
                # Try multiple session cookie names based on official documentation
                session_cookies = ["JSESSIONID", "OOSESSION", "sessionid"]

                for cookie_name in session_cookies:
                    # Check response cookies first
                    if hasattr(response, "cookies") and cookie_name in response.cookies:
                        cookie_value = response.cookies[cookie_name]
                        if cookie_value and not self.session_id:
                            self.session_id = cookie_value
                            logger.debug(
                                f"Session ID extracted from {cookie_name}: {self.session_id[:10]}..."
                            )
                            break

                    # Check Set-Cookie header
                    if "Set-Cookie" in response.headers:
                        cookie_header = response.headers["Set-Cookie"]
                        if cookie_name in cookie_header:
                            match = re.search(rf"{cookie_name}=([^;]+)", cookie_header)
                            if match and not self.session_id:
                                self.session_id = match.group(1)
                                logger.debug(
                                    f"Session ID extracted from header {cookie_name}: {self.session_id[:10]}..."
                                )
                                break

            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise OekoboxAuthenticationError(
                    f"HTTP {e.response.status_code}: Authentication failed",
                    e.response.status_code,
                ) from e
            elif e.response.status_code == 403:
                raise OekoboxAuthenticationError(
                    f"HTTP {e.response.status_code}: Access forbidden",
                    e.response.status_code,
                ) from e
            else:
                # Try to get error message from response
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", e.response.text)
                except Exception:
                    error_msg = e.response.text

                raise OekoboxAPIError(
                    f"HTTP {e.response.status_code}: {error_msg}",
                    e.response.status_code,
                ) from e

        except httpx.RequestError as e:
            raise OekoboxConnectionError(f"Connection error: {e}") from e

        # Parse response - handle both JSON and non-JSON responses
        try:
            data = response.json()
        except Exception as err:
            # If not JSON, try to create a basic success response
            if response.status_code == 200:
                data = {"result": "ok", "response_text": response.text}
            else:
                raise OekoboxAPIError(
                    f"Invalid response: {response.text}", response.status_code
                ) from err

        # Check for API-level errors in official response format
        if isinstance(data, dict) and "result" in data and data["result"] != "ok":
            result = data["result"]

            # Map official error codes to our exceptions
            if result in [
                "no_such_user",
                "wrong_password",
                "blocked",
                "duplicate_user",
            ]:
                raise OekoboxAuthenticationError(
                    f"Authentication failed: {result}", response.status_code
                )
            elif result in ["empty", "no_data"]:
                raise OekoboxValidationError(f"Validation error: {result}")
            else:
                raise OekoboxAPIError(f"API error: {result}", response.status_code)

        return data

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

    # Authentication methods - Fixed to match official API specification
    async def logon(self) -> UserInfo:
        """Authenticate with username and password using official 'logon' method.

        Official API endpoint: <urlbase>/api/logon?cid=<userid>&pass=<password>
        """
        url = f"{self.api_base_url}/logon"
        params = {
            "cid": self.username,  # Official API uses 'cid' for customer ID
            "pass": self.password,
        }

        try:
            data = await self._request("GET", url, params=params)

            # Official API response format: {"action": "Logon", "result": "ok", ...}
            if isinstance(data, dict) and data.get("action") == "Logon":
                if data.get("result") == "ok":
                    # Create UserInfo from successful login
                    return UserInfo(
                        id=None,
                        username=self.username,
                        email=self.username if "@" in self.username else None,
                        is_active=True,
                        pcgif_version=data.get("pcgifversion"),
                        shop_version=data.get("shopversion"),
                    )
                else:
                    # Handle specific error results from official API
                    result = data.get("result", "unknown_error")
                    raise OekoboxAuthenticationError(f"Login failed: {result}")

            # Fallback for unexpected response format
            return UserInfo(id=None, username=self.username, email=None, is_active=True)

        except OekoboxAuthenticationError:
            raise
        except Exception as e:
            raise OekoboxConnectionError(f"Failed to authenticate: {e}") from e

    # Maintain backward compatibility
    async def login(self) -> UserInfo:
        """Login method for backward compatibility. Use logon() for new code."""
        return await self.logon()

    async def logout(self) -> None:
        """Logout and clear session using official 'logout' method."""
        if self.session_id:
            try:
                url = f"{self.api_base_url}/logout"
                await self._request("GET", url)
            except Exception:
                # Continue even if logout request fails
                # Using pass here is acceptable for cleanup operations
                pass  # nosec B110
            finally:
                self.session_id = None

    # User and customer methods - Fixed to match official API
    async def get_user_info(self) -> UserInfo:
        """Get current user information."""
        url = f"{self.api_base_url}/user"
        data = await self._request("GET", url)
        try:
            return UserInfo(**data)
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid user data: {exc}") from exc

    async def get_customer_info(self) -> CustomerInfo:
        """Get customer profile information.

        Note: The API doesn't have a direct customer info endpoint.
        Customer information is typically retrieved via the dates1 endpoint.
        For now, return a basic CustomerInfo object.
        """
        # The official API doesn't have a direct /client endpoint for customer info
        # Customer info is retrieved via /dates1 endpoint which includes user context
        return CustomerInfo(
            id=self.username,
            user_info=UserInfo(
                username=self.username,
                email=self.username if "@" in self.username else None,
                is_active=True,
            ),
        )

    # Product catalog methods - Fixed to match API documentation
    async def get_groups(self) -> list[Group]:
        """Get product groups/categories using the correct API endpoint."""
        # According to API documentation: <baseurl>/api/groups2
        url = f"{self.api_base_url}/groups2"
        data = await self._request("GET", url)

        try:
            # Handle the documented response format: [{type:"Group", data:[[id,name,info,count]...]}]
            if isinstance(data, list) and len(data) > 0:
                groups = []
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "Group":
                        group_data = item.get("data", [])
                        for group_row in group_data:
                            if (
                                len(group_row) >= 4 and group_row[0] != 0
                            ):  # Skip special entries
                                groups.append(
                                    Group(
                                        id=str(group_row[0]),
                                        name=group_row[1],
                                        info=group_row[2] if group_row[2] else None,
                                        count=group_row[3],
                                    )
                                )
                return groups
            elif isinstance(data, list):
                return [Group(**item) for item in data]
            elif isinstance(data, dict) and "groups" in data:
                return [Group(**item) for item in data["groups"]]
            else:
                return []
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid group data: {exc}") from exc

    async def get_subgroups(self, group_id: str | None = None) -> list[SubGroup]:
        """Get product subgroups using the correct API endpoint."""
        # Based on groups endpoint, subgroups are included in the same response
        url = f"{self.api_base_url}/groups2"
        data = await self._request("GET", url)

        try:
            # Handle the documented response format for subgroups
            if isinstance(data, list) and len(data) > 1:
                subgroups = []
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "SubGroup":
                        subgroup_data = item.get("data", [])
                        for subgroup_row in subgroup_data:
                            if (len(subgroup_row) >= 4 and subgroup_row[0] != 0) and (
                                group_id is None or str(subgroup_row[2]) == group_id
                            ):  # Skip special entries and filter by group_id
                                subgroups.append(
                                    SubGroup(
                                        id=str(subgroup_row[0]),
                                        name=subgroup_row[1],
                                        parent_id=str(subgroup_row[2]),
                                        count=subgroup_row[3],
                                    )
                                )
                return subgroups
            elif isinstance(data, list):
                return [SubGroup(**item) for item in data]
            elif isinstance(data, dict) and "subgroups" in data:
                return [SubGroup(**item) for item in data["subgroups"]]
            else:
                return []
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid subgroup data: {exc}") from exc

    async def get_items(
        self,
        group_id: str | None = None,
        subgroup_id: str | None = None,
    ) -> list[Item]:
        """Get available items/products using the correct API endpoint."""
        # According to API documentation example: <urlbase>/api/items1/-1&hidden=1&timeless=1
        # The group_id should be part of the URL path, not a parameter
        if group_id:
            url = f"{self.api_base_url}/items1/{group_id}"
        else:
            url = f"{self.api_base_url}/items1/-1"  # -1 means all groups

        params = {}
        if subgroup_id:
            params["subgroup"] = subgroup_id

        data = await self._request("GET", url, params=params)
        try:
            # Handle the documented response format similar to groups
            if isinstance(data, list) and len(data) > 0:
                items = []
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "Item":
                        item_data = item.get("data", [])
                        for item_row in item_data:
                            if (
                                len(item_row) >= 4 and item_row[0] != 0
                            ):  # Skip terminating entries
                                items.append(
                                    Item(
                                        id=str(item_row[0]),
                                        name=item_row[1],
                                        price=float(item_row[2])
                                        if item_row[2]
                                        else None,
                                        description=item_row[4]
                                        if len(item_row) > 4
                                        else None,
                                        group_id=str(item_row[5])
                                        if len(item_row) > 5
                                        else None,
                                    )
                                )
                return items
            elif isinstance(data, list):
                return [Item(**item) for item in data]
            elif isinstance(data, dict) and "items" in data:
                return [Item(**item) for item in data["items"]]
            else:
                return []
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid item data: {exc}") from exc

    # Delivery methods - Fixed to match official API
    async def get_delivery_dates(self) -> list[DDate]:
        """Get available delivery dates using the correct API endpoint."""
        # According to API documentation: <baseurl>/dates1 but may need authentication
        # Try API endpoint first, then fallback to base URL
        try:
            url = f"{self.api_base_url}/dates1"
            data = await self._request("GET", url)
        except OekoboxAPIError as e:
            if e.status_code == 404:
                # Fallback to base URL endpoint
                url = f"{self.base_url}/dates1"
                data = await self._request("GET", url)
            else:
                raise

        try:
            # Handle the documented response format: ShopDate objects in array format
            dates: list[DDate] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "ShopDate":
                        date_data = item.get("data", [])
                        for date_row in date_data:
                            if (
                                len(date_row) >= 3 and date_row[0] != 0 and date_row[2]
                            ):  # Skip terminating entries and entries without dates
                                # Parse the date string from the API response
                                try:
                                    date_obj = datetime.fromisoformat(
                                        date_row[2].replace("Z", "+00:00")
                                    )
                                    dates.append(
                                        DDate(
                                            date=date_obj,
                                            is_available=True,  # Assume available if returned
                                            delivery_slots=[],
                                        )
                                    )
                                except (ValueError, IndexError):
                                    continue
            return dates
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid delivery date data: {exc}") from exc

    # Subscription methods - Updated to handle potential 404s gracefully
    async def get_subscriptions(self) -> list[Subscription]:
        """Get customer's active subscriptions."""
        # According to the API documentation, subscriptions are also available via the dates1 endpoint
        # But try the direct endpoint first
        try:
            url = f"{self.api_base_url}/client/subscriptions"
            data = await self._request("GET", url)
        except OekoboxAPIError as e:
            if e.status_code == 404:
                # Try to get subscriptions from dates1 endpoint
                try:
                    dates_url = f"{self.base_url}/dates1"
                    dates_data = await self._request("GET", dates_url)

                    # Extract subscriptions from dates response
                    subscriptions: list[Subscription] = []
                    if isinstance(dates_data, list):
                        for item in dates_data:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "Subscription"
                            ):
                                subscription_data = item.get("data", [])
                                for sub_row in subscription_data:
                                    if len(sub_row) >= 4 and sub_row[0] != 0:
                                        subscriptions.append(
                                            Subscription(
                                                id=str(sub_row[0]),
                                                customer_id=self.username,
                                                frequency=sub_row[2]
                                                if len(sub_row) > 2
                                                else None,
                                                is_active=True,
                                            )
                                        )
                    return subscriptions
                except Exception:
                    # If dates1 also fails, return empty list
                    return []
            else:
                raise

        try:
            if isinstance(data, list):
                return [Subscription(**item) for item in data]
            else:
                return [Subscription(**item) for item in data.get("subscriptions", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid subscription data: {exc}") from exc

    # Favorites methods - Updated to handle potential 404s gracefully
    async def get_favourites(self) -> list[Favourite]:
        """Get customer's favorite items."""
        # According to the API documentation, favourites are also available via the dates1 endpoint
        try:
            url = f"{self.api_base_url}/client/favourites"
            data = await self._request("GET", url)
        except OekoboxAPIError as e:
            if e.status_code == 404:
                # Try to get favourites from dates1 endpoint
                try:
                    dates_url = f"{self.base_url}/dates1"
                    dates_data = await self._request("GET", dates_url)

                    # Extract favourites from dates response
                    favourites: list[Favourite] = []
                    if isinstance(dates_data, list):
                        for item in dates_data:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "Favourite"
                            ):
                                favourite_data = item.get("data", [])
                                for fav_row in favourite_data:
                                    if len(fav_row) >= 2 and fav_row[0] == "Item":
                                        favourites.append(
                                            Favourite(
                                                customer_id=self.username,
                                                item_id=str(fav_row[1]),
                                            )
                                        )
                    return favourites
                except Exception:
                    # If dates1 also fails, return empty list
                    return []
            else:
                raise

        try:
            if isinstance(data, list):
                return [Favourite(**item) for item in data]
            else:
                return [Favourite(**item) for item in data.get("favourites", [])]
        except ValidationError as exc:
            raise OekoboxValidationError(f"Invalid favourites data: {exc}") from exc

    async def add_favourite(self, item_id: str) -> None:
        """Add item to favorites."""
        url = f"{self.api_base_url}/client/addfavourites"  # Official API method
        params = {
            "id": item_id
        }  # API documentation shows 'id' parameter, not 'item_id'
        await self._request("GET", url, params=params)

    async def remove_favourite(self, item_id: str) -> None:
        """Remove item from favorites."""
        url = f"{self.api_base_url}/client/dropfavourites"  # Official API method
        params = {
            "id": item_id
        }  # API documentation shows 'id' parameter, not 'item_id'
        await self._request("GET", url, params=params)

    # Shopping cart methods - Based on official API documentation
    async def get_cart(self) -> list[CartItem]:
        """Get current shopping cart contents."""
        url = f"{self.api_base_url}/cart/show"
        data = await self._request("GET", url)

        try:
            cart_items: list[CartItem] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "CartItem":
                        cart_data = item.get("data", [])
                        for cart_row in cart_data:
                            if (
                                len(cart_row) >= 4 and cart_row[0] != 0
                            ):  # Skip terminating entries
                                cart_items.append(
                                    CartItem(
                                        item_id=str(cart_row[0]),
                                        quantity=float(cart_row[1])
                                        if cart_row[1]
                                        else 1.0,
                                        unit=cart_row[2] if len(cart_row) > 2 else None,
                                        price=float(cart_row[3])
                                        if len(cart_row) > 3 and cart_row[3]
                                        else None,
                                        note=cart_row[4] if len(cart_row) > 4 else None,
                                    )
                                )
            return cart_items
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid cart data: {exc}") from exc

    async def add_to_cart(
        self,
        item_id: str,
        quantity: float = 1.0,
        unit: str | None = None,
        note: str | None = None,
    ) -> list[CartItem]:
        """Add an item to the shopping cart.

        Args:
            item_id: The ID of the item to add
            quantity: Amount to add (default: 1.0)
            unit: Unit specification (optional)
            note: Optional note for this cart position

        Returns:
            Updated cart contents
        """
        url = f"{self.api_base_url}/cart/add"
        params = {"id": item_id, "amount": str(quantity)}
        if unit:
            params["unit"] = unit
        if note:
            params["note"] = note

        try:
            data = await self._request("POST", url, params=params)
        except OekoboxAPIError as e:
            # Handle the specific "no_ddate" error which means no delivery date is selected
            if "no_ddate" in str(e):
                raise OekoboxValidationError(
                    "A delivery date must be selected before adding items to cart. Please select a delivery date first."
                ) from e
            else:
                raise

        try:
            cart_items: list[CartItem] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "CartItem":
                        cart_data = item.get("data", [])
                        for cart_row in cart_data:
                            if len(cart_row) >= 4 and cart_row[0] != 0:
                                cart_items.append(
                                    CartItem(
                                        item_id=str(cart_row[0]),
                                        quantity=float(cart_row[1])
                                        if cart_row[1]
                                        else 1.0,
                                        unit_price=float(cart_row[3])
                                        if len(cart_row) > 3 and cart_row[3]
                                        else None,
                                        total_price=float(cart_row[3])
                                        * float(cart_row[1])
                                        if len(cart_row) > 3
                                        and cart_row[3]
                                        and cart_row[1]
                                        else None,
                                    )
                                )
            return cart_items
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid cart data: {exc}") from exc

    async def remove_from_cart(
        self, item_id: str | None = None, position: int | None = None
    ) -> list[CartItem]:
        """Remove an item from the shopping cart.

        Args:
            item_id: The ID of the item to remove (alternative to position)
            position: Cart position to remove (alternative to item_id)

        Returns:
            Updated cart contents
        """
        url = f"{self.api_base_url}/cart/remove"
        params = {}

        if item_id:
            params["id"] = item_id
        elif position is not None:
            params["pos"] = str(position)
        else:
            raise ValueError("Either item_id or position must be provided")

        data = await self._request("POST", url, params=params)

        try:
            cart_items: list[CartItem] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "CartItem":
                        cart_data = item.get("data", [])
                        for cart_row in cart_data:
                            if len(cart_row) >= 4 and cart_row[0] != 0:
                                cart_items.append(
                                    CartItem(
                                        item_id=str(cart_row[0]),
                                        quantity=float(cart_row[1])
                                        if cart_row[1]
                                        else 1.0,
                                        unit=cart_row[2] if len(cart_row) > 2 else None,
                                        price=float(cart_row[3])
                                        if len(cart_row) > 3 and cart_row[3]
                                        else None,
                                        note=cart_row[4] if len(cart_row) > 4 else None,
                                    )
                                )
            return cart_items
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid cart data: {exc}") from exc

    async def clear_cart(self) -> None:
        """Clear the shopping cart by using the client resetcart method."""
        url = f"{self.api_base_url}/client/resetcart"
        try:
            await self._request("GET", url)
            # The resetcart endpoint may return an empty response or just "ok"
            # We consider it successful if no exception was raised
        except OekoboxAPIError as e:
            # Handle the case where the API returns an empty result string
            if "API error:" in str(e) and e.status_code == 200:
                # This is likely an empty response which should be considered success
                pass
            else:
                raise

    # Individual item methods
    async def get_item(self, item_id: str) -> Item:
        """Get detailed information about a specific item."""
        # Try multiple endpoints for getting individual items
        urls_to_try = [
            f"{self.api_base_url}/item/{item_id}",
            f"{self.base_url}/item/{item_id}",
            f"{self.api_base_url}/items1/-1",  # Get all items and filter
        ]

        for url in urls_to_try:
            try:
                data = await self._request("GET", url)

                # Handle the documented response format for single items
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if isinstance(item, dict) and item.get("type") == "Item":
                            item_data = item.get("data", [])
                            for item_row in item_data:
                                if len(item_row) >= 4 and str(item_row[0]) == item_id:
                                    return Item(
                                        id=str(item_row[0]),
                                        name=item_row[1],
                                        price=float(item_row[2])
                                        if item_row[2]
                                        else None,
                                        description=item_row[4]
                                        if len(item_row) > 4
                                        else None,
                                        group_id=str(item_row[5])
                                        if len(item_row) > 5
                                        else None,
                                        unit=item_row[3] if len(item_row) > 3 else None,
                                    )
                elif isinstance(data, dict):
                    return Item(**data)

            except OekoboxAPIError as e:
                if e.status_code == 404:
                    continue  # Try next URL
                else:
                    raise

        # If no direct item endpoint works, try to get from all items
        try:
            items = await self.get_items()
            for item in items:
                if item.id == item_id:
                    return item
        except Exception:
            # Using pass here is acceptable for fallback behavior
            pass  # nosec B110

        raise OekoboxValidationError(f"Item not found: {item_id}")

    # Order methods - Based on official API documentation
    async def get_orders(self) -> list[Order]:
        """Get customer's order history."""
        # Try different endpoints that might provide orders
        try:
            # First try the dates1 endpoint which includes ShopDate objects (orders)
            url = f"{self.base_url}/dates1"
            data = await self._request("GET", url)

            orders: list[Order] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "ShopDate":
                        shopdate_data = item.get("data", [])
                        for order_row in shopdate_data:
                            if (
                                len(order_row) >= 8
                                and order_row[0] != -1
                                and order_row[0] != 0
                            ):  # Valid order IDs
                                # Parse delivery date from the ShopDate format
                                delivery_date = None
                                if len(order_row) > 2 and order_row[2]:
                                    with suppress(ValueError, TypeError):
                                        delivery_date = datetime.fromisoformat(
                                            order_row[2]
                                        ).date()

                                orders.append(
                                    Order(
                                        id=str(order_row[0]),
                                        customer_id=self.username,
                                        delivery_date=delivery_date,
                                        status=order_row[1]
                                        if len(order_row) > 1
                                        else None,
                                        total=float(order_row[9])
                                        if len(order_row) > 9 and order_row[9]
                                        else None,
                                    )
                                )
            return orders

        except OekoboxAPIError:
            # Fallback to empty list if endpoint not available
            return []

    async def get_order(self, order_id: str) -> Order:
        """Get detailed information about a specific order."""
        url = f"{self.api_base_url}/order2/{order_id}"

        try:
            data = await self._request("GET", url)
        except OekoboxAPIError as e:
            if e.status_code == 404:
                raise OekoboxValidationError(f"Order not found: {order_id}") from e
            else:
                raise

        try:
            # Handle the documented response format for orders
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "Order":
                        order_data = item.get("data", [])
                        if len(order_data) > 0 and len(order_data[0]) >= 2:
                            order_row = order_data[0]
                            from datetime import datetime

                            delivery_date = None
                            if len(order_row) > 1 and order_row[1]:
                                with suppress(ValueError, TypeError):
                                    delivery_date = datetime.fromisoformat(
                                        order_row[1]
                                    ).date()

                            return Order(
                                id=str(order_row[0]),
                                customer_id=self.username,
                                delivery_date=delivery_date,
                                status=order_row[2] if len(order_row) > 2 else None,
                                total=None,  # Total might be calculated from positions
                            )
            elif isinstance(data, dict):
                return Order(**data)

            raise OekoboxValidationError(f"Order not found in response: {order_id}")
        except (ValidationError, IndexError, KeyError) as exc:
            raise OekoboxValidationError(f"Invalid order data: {exc}") from exc
